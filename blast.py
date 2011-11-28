""" Adhoc web resource.

BLAST web resources and tools.
"""

import os
import json
import subprocess
import logging

from wrapid.resource import *
from wrapid.fields import *
from wrapid.json_representation import JsonRepresentation
from wrapid.text_representation import TextRepresentation

from . import configuration
from .method_mixin import *
from .html_representation import *


BLASTDB = os.path.join(configuration.DB_DIR, 'blast')
os.environ['BLASTDB'] = BLASTDB


def get_databases(type, account_teams):
    infile = open(os.path.join(BLASTDB, "%s_databases.json" % type))
    databases = json.load(infile)
    infile.close()
    result = []
    for db in databases:
        try:
            teams = set(db['teams'])
        except KeyError:                # No database teams means public
            pass
        else:
            if not teams.intersection(account_teams): continue
        result.append(db)
    return configuration.rstr(result)


OUTPUT_FORMATS = [dict(value='0',
                       title='Pairwise',
                       mimetype='text/plain'),
                  dict(value='1',
                       title='Query-anchored showing identities',
                       mimetype='text/plain'),
                  dict(value='2',
                       title='Query-anchored no identities',
                       mimetype='text/plain'),
                  dict(value='3',
                       title='Flat query-anchored, show identities',
                       mimetype='text/plain'),
                  dict(value='4',
                       title='Flat query-anchored, no identities',
                       mimetype='text/plain'),
                  dict(value='5',
                       title='XML Blast output',
                       mimetype='application/xml'),
                  dict(value='6',
                       title='Tab-separated values',
                       mimetype='text/tab-separated-values'),
                  dict(value='7',
                       title='Tab-separated values with comment lines',
                       mimetype='text/tab-separated-values'),
                  dict(value='8',
                       title='Text ASN.1',
                       mimetype='text/plain'),
                  dict(value='10',
                       title='Comma-separated values',
                       mimetype='text/csv'),
                  dict(value='11',
                       title='BLAST archive format (ASN.1)',
                       mimetype='text/plain')]

# 2011-07-14 from http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi
GENETIC_CODES = [dict(value='1', title='Standard'),
                 dict(value='2', title='Vertebrate Mitochondrial'),
                 dict(value='3', title='Yeast Mitochondrial'),
                 dict(value='4', title='Mold Mitochondrial; Protozoan Mitochondrial; Coelenterate Mitochondrial; Mycoplasma; Spiroplasma'),
                 dict(value='5', title='Invertebrate Mitochondrial'),
                 dict(value='6', title='Ciliate Nuclear; Dasycladacean Nuclear; Hexamita Nuclear'),
                 dict(value='9', title='Echinoderm Mitochondrial; Flatworm Mitochondrial'),
                 dict(value='10', title='Euplotid Nuclear'),
                 dict(value='11', title='Bacterial and Plant Plastid'),
                 dict(value='12', title='Alternative Yeast Nuclear'),
                 dict(value='13', title='Ascidian Mitochondrial'),
                 dict(value='14', title='Alternative Flatworm Mitochondrial'),
                 dict(value='15', title='Blepharisma Macronuclear'),
                 dict(value='16', title='Chlorophycean Mitochondrial'),
                 dict(value='21', title='Trematode Mitochondrial'),
                 dict(value='22', title='Scenedesmus obliquus Mitochondrial'),
                 dict(value='23', title='Thraustochytrium Mitochondrial')]


class BlastHtmlRepresentation(HtmlRepresentation):
    "Common HTML representation of the BLAST task create page."

    def get_content(self):
        return self.get_form_panel(funcs=dict(db=self.get_db_multiselect),
                                   submit='Create and execute task')

    def get_db_multiselect(self, field, current=None):
        "Custom HTML for the 'db' multiselect field."
        if not current: current = []
        rows = [TR(TH('Search'),
                   TH('Database'),
                   TH('# sequences'),
                   TH('Total size'),
                   TH('Updated'))]
        for option in field['options']:
            rows.append(TR(TD(INPUT(type='checkbox',
                                    name=field['name'],
                                    value=option['value'],
                                    checked=option['value'] in current)),
                           TD(option['title']),
                           TD(option['number'], klass='number'),
                           TD(option['size'], klass='number'),
                           TD(option['updated'])))
        return TABLE(klass='list', *rows)


class GET_BlastCreate(GET_Mixin, GET):
    "Return the page for creating a BLAST task."

    tool = None
    database_type = None
    fields = None

    def __init__(self):
        super(GET_BlastCreate, self).__init__(
            outreprs=[JsonRepresentation(),
                      TextRepresentation(),
                      BlastHtmlRepresentation()])

    def descr(self):
        raise NotImplementedError

    def add_data(self, data, resource, request, application):
        self.allow_access()
        if self.login.max_tasks >= 0:
            count, size = self.get_tasks_stats(self.login.name)
            if count >= self.login.max_tasks:
                raise HTTP_CONFLICT('max number of tasks reached')
        data['entity'] = 'tool'
        data['title'] = "%s task creation" % self.tool
        data['descr'] = self.descr()
        databases = []
        for db in get_databases(self.database_type, self.login.teams):
            db.pop('teams', None)
            db['value'] = db.pop('filename')
            databases.append(db)
        fill = dict(db=dict(options=databases))
        default = self.login.preferences.get(self.tool, dict())
        data['tool'] = dict(name=self.tool,
                            fields=self.fields.get_data(fill=fill,
                                                        default=default),
                            title='Enter query and select parameters',
                            href=resource.get_url(),
                            cancel=application.get_url())


class POST_TaskCreate(POST_Mixin, POST):
    "Actually create a BLAST task."

    tool = None

    def action(self, resource, request, application):
        "Handle the request and return a response instance."
        self.allow_access()
        if self.login.max_tasks >= 0:
            count, size = self.get_tasks_stats(self.login.name)
            if count >= self.login.max_tasks:
                raise HTTP_CONFLICT('max number of tasks reached')
        self.inputs = self.infields.parse(request)
        from .task import Task
        self.task = Task(self.cnx)
        self.task.href = application.get_url('task', self.task.iui)
        self.task.tool = self.tool
        self.new_preferences = dict()
        self.task.title = self.inputs.get('title')
        self.new_preferences['title'] = self.task.title
        self.task.data['parameters'] = dict()
        self.set_data()
        self.execute_task()
        self.update_account_preferences()
        raise HTTP_SEE_OTHER(Location=self.task.href)

    def set_data(self):
        raise NotImplementedError

    def set_db(self):
        db = self.inputs['db']
        self.task.data['parameters']['-db'] = ' '.join(db)
        self.new_preferences['db'] = db

    def set_query(self, query_type):
        query = self.inputs['query_file']
        logging.debug("query_file %s", query)
        if not query:
            query = self.inputs['query_content']
            logging.debug("query_content %s", query)
        if query is None:
            raise HTTP_BAD_REQUEST('no query specified')
        if query:
            if query[0] != '>':   # Add FASTA header line
                query = ">query\n%s" % query
        else:
            raise HTTP_BAD_REQUEST('no content in query file nor in field')
        characters = set()
        for line in query.split('\n'):
            line = line.strip()
            if not line: continue
            if line[0] == '>': continue # FASTA header line
            characters.update(line.upper())
        if query_type == 'protein':
            if not characters.difference('ACTG'):
                raise HTTP_BAD_REQUEST('query appears to be nucleotide')
        elif query_type == 'nucleotide':
            if characters.difference('ACTGX'):
                raise HTTP_BAD_REQUEST('query appears to be protein')
        else:
            raise ValueError('invalid query_type')
        self.task.data['query'] = query

    def set_db_gencode(self):
        try:
            db_gencode = self.inputs['db_gencode']
            self.task.data['parameters']['-db_gencode'] = db_gencode
            self.new_preferences['db_gencode'] = db_gencode
        except KeyError:
            pass

    def set_query_gencode(self):
        try:
            query_gencode = self.inputs['query_gencode']
            self.task.data['parameters']['-query_gencode'] = query_gencode
            self.new_preferences['query_gencode'] = query_gencode
        except KeyError:
            pass

    def set_dust(self):
        try:
            dust = self.inputs['dust']
            self.task.data['parameters']['-dust'] = dust
            self.new_preferences['dust'] = dust
        except KeyError:
            pass

    def set_seg(self):
        try:
            seg = self.inputs['seg']
            self.task.data['parameters']['-seg'] = seg
            self.new_preferences['seg'] = seg
        except KeyError:
            pass

    def set_task_type(self):
        try:
            task_type = self.inputs['task_type']
            self.task.data['parameters']['-task'] = task_type
            self.new_preferences['task_type'] = task_type
        except KeyError:
            pass

    def set_evalue(self):
        try:
            evalue = self.inputs['evalue']
            if evalue <= 0.0:
                raise HTTP_BAD_REQUEST('invalid E-value')
            self.task.data['parameters']['-evalue'] = evalue
            self.new_preferences['evalue'] = evalue
        except KeyError:
            pass

    def set_output_format(self):
        try:
            outfmt = self.inputs['outfmt']
            self.task.data['parameters']['-outfmt'] = outfmt
            self.new_preferences['outfmt'] = outfmt
        except KeyError:
            pass

    def set_num_descriptions(self):
        try:
            number = self.inputs['num_descriptions']
            if number < 0:
                raise HTTP_BAD_REQUEST('invalid # seq descriptions')
            self.task.data['parameters']['-num_descriptions'] = number
            self.new_preferences['num_descriptions'] = number
        except KeyError:
            pass

    def set_num_alignments(self):
        try:
            number = self.inputs['num_alignments']
            if number < 0:
                raise HTTP_BAD_REQUEST('invalid # seq alignments')
            self.task.data['parameters']['-num_alignments'] = number
            self.new_preferences['num_alignments'] = number
        except KeyError:
            pass

    def execute_task(self):
        self.task.create(self.login.id)
        process = subprocess.Popen([configuration.PYTHON,
                                    configuration.EXECUTE_SCRIPT,
                                    self.task.iui])
        process.wait()                  # Only waits for daemonize to finish


BLASTN_FIELDS = Fields(StringField('title', title='Title', length=30,
                              descr='Descriptive title for the task.'),
                       MultiSelectField('db', title='Database',
                                        required=True, check=False,
                                        descr='Check the nucleotide database(s)'
                                              ' to search.'),
                       FileField('query_file', title='Query file',
                                 descr='Upload file containing query nucleotide'
                                 ' sequence(s) in FASTA format.'),
                       TextField('query_content', title='Query',
                                 descr='Query nucleotide sequence(s) in FASTA'
                                 ' format. This data is used only if no file'
                                 ' is specified in the field above.'),
                       SelectField('dust', title='DUST filter',
                                   options=['yes', 'no', '20 64 1'],
                                   required=True, default='no', check=True,
                                   descr='Filter out low-complexity regions'
                                   ' from the query sequence.'),
                       SelectField('task_type', title='Task type',
                                   required=True, default='blastn',
                                   options=
                                   [dict(value='blastn',
                                         title='blastn: traditional, requiring'
                                          ' an exact match of 11'),
                                    dict(value='blastn-short',
                                         title='blastn-short: optimized for'
                                         ' sequences shorter than 50 bases'),
                                    dict(value='megablast',
                                         title='megablast: to find very similar'
                                         ' sequences'),
                                    dict(value='dc-megablast',
                                         title='dc-megablast: discontiguous'
                                         ' megablast to find more distant'
                                         ' sequences')],
                                   descr='Variant of blastn task.'),
                       FloatField('evalue', title='E-value',
                                  required=True, default=10.0,
                                  descr='Expectation value threshold.'),
                       SelectField('outfmt', title='Output format',
                                   options=OUTPUT_FORMATS,
                                   required=True, default='0', check=True,
                                   descr='Format of search results.'),
                       IntegerField('num_descriptions',
                                    title='# seq descriptions',
                                    default=500,
                                    descr='Number of one-line descriptions'
                                    ' to show in the output.'),
                       IntegerField('num_alignments',
                                    title='# alignments',
                                    default=250,
                                    descr='Number of alignments to show in'
                                    ' the output.'),
                       CheckboxField('set_preferences', title='Set preferences',
                                     default=False,
                                     text='Set the above values to become your'
                                     ' defaults for this tool.'))


class GET_BlastnCreate(GET_BlastCreate):
    "Return the page for creating a 'blastn' task."

    tool = 'blastn'
    database_type = 'nucleotide'
    fields = BLASTN_FIELDS

    def descr(self):
        return '''BLAST search in a **nucleotide database** using a **nucleotide query**. Executable version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' % configuration.BLAST_VERSION


class POST_BlastnCreate(POST_TaskCreate):
    """Create and execute a 'blastn' task.
    The response is a HTTP 303 'See Other' redirection to the URL of the task.
    """

    tool = 'blastn'

    def __init__(self):
        super(POST_BlastnCreate, self).__init__(infields=BLASTN_FIELDS,
                                                descr=self.__doc__)

    def set_data(self):
        self.set_db()
        self.set_query('nucleotide')
        self.set_dust()
        self.set_task_type()
        self.set_evalue()
        self.set_output_format()
        self.set_num_descriptions()
        self.set_num_alignments()


BLASTP_FIELDS = Fields(StringField('title', title='Title', length=30,
                              descr='Descriptive title for the task.'),
                       MultiSelectField('db', title='Database',
                                        required=True, check=False,
                                        descr='Check the protein database(s)'
                                              ' to search.'),
                       FileField('query_file', title='Query file',
                                 descr='Upload file containing query protein'
                                 ' sequence(s) in FASTA format.'),
                       TextField('query_content', title='Query',
                                 descr='Query protein sequence(s) in FASTA'
                                 ' format. This data is used only if no file'
                                 ' is specified in the field above.'),
                       SelectField('seg', title='SEG filter',
                                   options=['yes', 'no', '12 2.2 2.5'],
                                   default='no', check=True,
                                   descr='Filter out low-complexity regions'
                                   ' from the query sequence.'),
                       SelectField('task_type', title='Task type',
                                   required=True, default='blastp',
                                   options=
                                   [dict(value='blastp',
                                         title='blastp: traditional, to'
                                          ' compare proteins'),
                                    dict(value='blastp-short',
                                         title='blastp-short: optimized for'
                                         ' sequences shorter than 30 residues')],
                                   descr='Variant of blastp task.'),
                       FloatField('evalue', title='E-value',
                                  required=True, default=10.0,
                                  descr='Expectation value threshold.'),
                       SelectField('outfmt', title='Output format',
                                   options=OUTPUT_FORMATS,
                                   required=True, default='0', check=True,
                                   descr='Format of search results.'),
                       IntegerField('num_descriptions',
                                    title='# seq descriptions',
                                    default=500,
                                    descr='Number of one-line descriptions'
                                    ' to show in the output.'),
                       IntegerField('num_alignments',
                                    title='# alignments',
                                    default=250,
                                    descr='Number of alignments to show in'
                                    ' the output.'),
                       CheckboxField('set_preferences', title='Set preferences',
                                     default=False,
                                     text='Set the above values to become your'
                                     ' defaults for this tool.'))
                       

class GET_BlastpCreate(GET_BlastCreate):
    "Return the page for creating a 'blastp' task."

    tool = 'blastp'
    database_type = 'protein'
    fields = BLASTP_FIELDS

    def descr(self):
        return '''BLAST search in a **protein database** using a **protein query**. Executable version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' % configuration.BLAST_VERSION


class POST_BlastpCreate(POST_TaskCreate):
    """Create and execute a 'blastp' task.
    The response is a HTTP 303 'See Other' redirection to the URL of the task.
    """

    tool = 'blastp'

    def __init__(self):
        super(POST_BlastpCreate, self).__init__(infields=BLASTP_FIELDS,
                                                descr=self.__doc__)

    def set_data(self):
        self.set_db()
        self.set_query('protein')
        self.set_task_type()
        self.set_seg()
        self.set_evalue()
        self.set_output_format()
        self.set_num_descriptions()
        self.set_num_alignments()


BLASTX_FIELDS = Fields(StringField('title', title='Title', length=30,
                              descr='Descriptive title for the task.'),
                       MultiSelectField('db', title='Database',
                                        required=True, check=False,
                                        descr='Check the protein database(s)'
                                              ' to search.'),
                       FileField('query_file', title='Query file',
                                 descr='Upload file containing query nucleotide'
                                 ' sequence(s) in FASTA format.'),
                       TextField('query_content', title='Query',
                                 descr='Query nucleotide sequence(s) in FASTA'
                                 ' format. This data is used only if no file'
                                 ' is specified in the field above.'),
                       SelectField('query_gencode', title='Query genetic code',
                                   options=GENETIC_CODES,
                                   default='1',
                                   descr='Genetic code to use for translating'
                                   ' the nucleotide query into protein.'),
                       SelectField('seg', title='SEG filter',
                                   options=['yes', 'no', '12 2.2 2.5'],
                                   required=True, default='12 2.2 2.5',
                                   check=True,
                                   descr='Filter out low-complexity regions'
                                   ' from the query sequence.'),
                       FloatField('evalue', title='E-value',
                                  required=True, default=10.0,
                                  descr='Expectation value threshold.'),
                       SelectField('outfmt', title='Output format',
                                   options=OUTPUT_FORMATS,
                                   required=True, default='0', check=True,
                                   descr='Format of search results.'),
                       IntegerField('num_descriptions',
                                    title='# seq descriptions',
                                    default=500,
                                    descr='Number of one-line descriptions'
                                    ' to show in the output.'),
                       IntegerField('num_alignments',
                                    title='# alignments',
                                    default=250,
                                    descr='Number of alignments to show in'
                                    ' the output.'),
                       CheckboxField('set_preferences', title='Set preferences',
                                     default=False,
                                     text='Set the above values to become your'
                                     ' defaults for this tool.'))
                       

class GET_BlastxCreate(GET_BlastCreate):
    "Return the page for creating a 'blastx' task."

    tool = 'blastx'
    database_type = 'protein'
    fields = BLASTX_FIELDS

    def descr(self):
        return '''BLAST search in a **protein database** using a **translated nucleotide query**. Executable version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' % configuration.BLAST_VERSION


class POST_BlastxCreate(POST_TaskCreate):
    """Create and execute a 'blastx' task.
    The response is a HTTP 303 'See Other' redirection to the URL of the task.
    """

    tool = 'blastx'

    def __init__(self):
        super(POST_BlastxCreate, self).__init__(infields=BLASTX_FIELDS,
                                                descr=self.__doc__)

    def set_data(self):
        self.set_db()
        self.set_query('nucleotide')
        self.set_query_gencode()
        self.set_seg()
        self.set_evalue()
        self.set_output_format()
        self.set_num_descriptions()
        self.set_num_alignments()


TBLASTN_FIELDS = Fields(StringField('title', title='Title', length=30,
                              descr='Descriptive title for the task.'),
                       MultiSelectField('db', title='Database',
                                        required=True, check=False,
                                        descr='Check the nucleotide database(s)'
                                              ' to search.'),
                       SelectField('db_gencode', title='Database genetic code',
                                   options=GENETIC_CODES,
                                   default='1',
                                   descr='Genetic code to use for translating'
                                   ' the nucleotide database into protein.'),
                       FileField('query_file', title='Query file',
                                 descr='Upload file containing query protein'
                                 ' sequence(s) in FASTA format.'),
                       TextField('query_content', title='Query',
                                 descr='Query protein sequence(s) in FASTA'
                                 ' format. This data is used only if no file'
                                 ' is specified in the field above.'),
                       SelectField('seg', title='SEG filter',
                                   options=['yes', 'no', '12 2.2 2.5'],
                                   required=True, default='12 2.2 2.5',
                                   check=True,
                                   descr='Filter out low-complexity regions'
                                   ' from the query sequence.'),
                       FloatField('evalue', title='E-value',
                                  required=True, default=10.0,
                                  descr='Expectation value threshold.'),
                       SelectField('outfmt', title='Output format',
                                   options=OUTPUT_FORMATS,
                                   required=True, default='0', check=True,
                                   descr='Format of search results.'),
                       IntegerField('num_descriptions',
                                    title='# seq descriptions',
                                    default=500,
                                    descr='Number of one-line descriptions'
                                    ' to show in the output.'),
                       IntegerField('num_alignments',
                                    title='# alignments',
                                    default=250,
                                    descr='Number of alignments to show in'
                                    ' the output.'),
                       CheckboxField('set_preferences', title='Set preferences',
                                     default=False,
                                     text='Set the above values to become your'
                                     ' defaults for this tool.'))
                       

class GET_TblastnCreate(GET_BlastCreate):
    "Return the page for creating a 'tblastn' task."

    tool = 'tblastn'
    database_type = 'nucleotide'
    fields = TBLASTN_FIELDS

    def descr(self):
        return '''BLAST search in a **translated nucleotide database** using a **protein query**. Executable version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' % configuration.BLAST_VERSION


class POST_TblastnCreate(POST_TaskCreate):
    """Create and execute a 'tblastn' task.
    The response is a HTTP 303 'See Other' redirection to the URL of the task.
    """

    tool = 'tblastn'

    def __init__(self):
        super(POST_TblastnCreate, self).__init__(infields=TBLASTN_FIELDS,
                                                descr=self.__doc__)

    def set_data(self):
        self.set_db()
        self.set_db_gencode()
        self.set_query('protein')
        self.set_seg()
        self.set_evalue()
        self.set_output_format()
        self.set_num_descriptions()
        self.set_num_alignments()


TBLASTX_FIELDS = Fields(StringField('title', title='Title', length=30,
                              descr='Descriptive title for the task.'),
                       MultiSelectField('db', title='Database',
                                        required=True, check=False,
                                        descr='Check the nucleotide database(s)'
                                              ' to search.'),
                       SelectField('db_gencode', title='Database genetic code',
                                   options=GENETIC_CODES,
                                   default='1',
                                   descr='Genetic code to use for translating'
                                   ' the nucleotide database into protein.'),
                       FileField('query_file', title='Query file',
                                 descr='Upload file containing query nucleotide'
                                 ' sequence(s) in FASTA format.'),
                       TextField('query_content', title='Query',
                                 descr='Query nucleotide sequence(s) in FASTA'
                                 ' format. This data is used only if no file'
                                 ' is specified in the field above.'),
                       SelectField('query_gencode', title='Query genetic code',
                                   options=GENETIC_CODES,
                                   default='1',
                                   descr='Genetic code to use for translating'
                                   ' the nucleotide query into protein.'),
                       SelectField('seg', title='SEG filter',
                                   options=['yes', 'no', '12 2.2 2.5'],
                                   required=True, default='12 2.2 2.5',
                                   check=True,
                                   descr='Filter out low-complexity regions'
                                   ' from the query sequence.'),
                       FloatField('evalue', title='E-value',
                                  required=True, default=10.0,
                                  descr='Expectation value threshold.'),
                       SelectField('outfmt', title='Output format',
                                   options=OUTPUT_FORMATS,
                                   required=True, default='0', check=True,
                                   descr='Format of search results.'),
                       IntegerField('num_descriptions',
                                    title='# seq descriptions',
                                    default=500,
                                    descr='Number of one-line descriptions'
                                    ' to show in the output.'),
                       IntegerField('num_alignments',
                                    title='# alignments',
                                    default=250,
                                    descr='Number of alignments to show in'
                                    ' the output.'),
                       CheckboxField('set_preferences', title='Set preferences',
                                     default=False,
                                     text='Set the above values to become your'
                                     ' defaults for this tool.'))
                       

class GET_TblastxCreate(GET_BlastCreate):
    "Return the page for creating a 'tblastx' task."

    tool = 'tblastx'
    database_type = 'nucleotide'
    fields = TBLASTX_FIELDS

    def descr(self):
        return '''BLAST search in a **translated nucleotide database** using a **translated nucleotide query**. Executable version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' % configuration.BLAST_VERSION


class POST_TblastxCreate(POST_TaskCreate):
    """Create and execute a 'tblastx' task.
    The response is a HTTP 303 'See Other' redirection to the URL of the task.
    """

    tool = 'tblastx'

    def __init__(self):
        super(POST_TblastxCreate, self).__init__(infields=TBLASTX_FIELDS,
                                                descr=self.__doc__)

    def set_data(self):
        self.set_db()
        self.set_db_gencode()
        self.set_query('nucleotide')
        self.set_query_gencode()
        self.set_seg()
        self.set_evalue()
        self.set_output_format()
        self.set_num_descriptions()
        self.set_num_alignments()


class BlastTool(object):
    "General BLAST tool; actually execute the task."

    def __init__(self, tool):
        self.tool = tool

    def __call__(self, task):
        assert task.tool == self.tool
        assert task.status == configuration.EXECUTING
        args = [os.path.join(configuration.BLAST_PATH, self.tool)]
        for key, value in task.data['parameters'].items():
            args.append(key)
            args.append(str(value))
        command = [self.tool]
        for key, value in task.data['parameters'].items():
            command.append(key)
            value = str(value)
            if len(value.split()) > 1:
                value = "'%s'" % value
            command.append(value)
        task.data['command'] = ' '.join(command)
        task.save()
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(input=task.data['query'])
        task.data['output'] = stdout
        outfmt = task.data['parameters'].get('-outfmt')
        for item in OUTPUT_FORMATS:
            if item['value'] == outfmt:
                task.data['output_content_type'] = item['mimetype']
                break
        else:
            task.data['output_content_type'] = 'text/plain'
        task.data['error'] = stderr
        if process.returncode > 0:
            task.status = configuration.FAILED
        elif process.returncode < 0:
            task.status = configuration.KILLED
        else:
            task.status = configuration.FINISHED


configuration.add_tool('BLAST', 'blastn', BlastTool('blastn'))
configuration.add_tool('BLAST', 'blastp', BlastTool('blastp'))
configuration.add_tool('BLAST', 'blastx', BlastTool('blastx'))
configuration.add_tool('BLAST', 'tblastn', BlastTool('tblastn'))
configuration.add_tool('BLAST', 'tblastx', BlastTool('tblastx'))


def setup(application):
    "Setup the web application interface."
    application.append(Resource('/blastn', name='blastn',
                                GET=GET_BlastnCreate(),
                                POST=POST_BlastnCreate(),
                                descr='Blastn task: nucleotide query'
                                ' against a nucleotide database.'))
    application.append(Resource('/blastp', name='blastp',
                                GET=GET_BlastpCreate(),
                                POST=POST_BlastpCreate(),
                                descr='Blastp task: protein query'
                                ' against a protein database.'))
    application.append(Resource('/blastx', name='blastx',
                                GET=GET_BlastxCreate(),
                                POST=POST_BlastxCreate(),
                                descr='Blastp task: translated nucleotide'
                                ' query against a protein database.'))
    application.append(Resource('/tblastn', name='tblastn',
                                GET=GET_TblastnCreate(),
                                POST=POST_TblastnCreate(),
                                descr='Tblastn task: protein query against'
                                ' a translated nucleotide database.'))
    application.append(Resource('/tblastx', name='tblastx',
                                GET=GET_TblastxCreate(),
                                POST=POST_TblastxCreate(),
                                descr='Tblastx task: translated nucleotide'
                                ' query against a translated nucleotide'
                                ' database.'))
