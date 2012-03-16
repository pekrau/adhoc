""" Adhoc: Simple web application for task execution.

BLAST web resources and tools.
"""

import os
import json
import subprocess

from wrapid.utils import rstr

from .method_mixin import *
from .representation import *


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
        except KeyError:                # Unspecified teams means public
            pass
        else:
            if not teams.intersection(account_teams): continue
        result.append(db)
    return rstr(result)


class DbMultiSelectField(MultiSelectField):
    type = 'db_multiselect'


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


class BlastHtmlRepresentation(FormHtmlRepresentation):
    "Common HTML representation of the BLAST task create page."

    def get_element_db_multiselect(self, field, default=None):
        "Custom HTML for the 'db' multiselect field."
        rows = [TR(TH('Search'),
                   TH('Database'),
                   TH('# sequences'),
                   TH('Total size'),
                   TH('Updated'))]
        if not default: default = []
        for option in field['options']:
            rows.append(TR(TD(INPUT(type='checkbox',
                                    name=field['name'],
                                    value=option['value'],
                                    checked=option['value'] in default)),
                           TD(option['title']),
                           TD(option['number'], klass='integer'),
                           TD(option['size'], klass='integer'),
                           TD(option['updated'], klass='integer')))
        return TABLE(klass='list', *rows)


class GET_BlastCreate(ToolMixin, MethodMixin, GET):
    "Display the BLAST tool form to create a task."

    database_type = None

    outreprs = [JsonRepresentation,
                TextRepresentation,
                BlastHtmlRepresentation]

    fields = ()

    def set_current(self, resource, request, application):
        self.check_quota(resource, request, application)

    def get_data_resource(self, resource, request, application):
        data = dict(resource="Tool %s" % self.tool,
                    title="%s task creation" % self.tool,
                    descr=self.descr)
        databases = []
        for db in get_databases(self.database_type, self.login['teams']):
            db.pop('teams', None)
            db['value'] = db.pop('filename')
            databases.append(db)
        fields=self.get_data_fields(fill=dict(db=dict(options=databases)),
                                    default=self.get_preferences())
        data['form'] = dict(tool=self.tool,
                            fields=fields,
                            label='Create task and execute',
                            title='Enter query and select parameters',
                            href=resource.url,
                            cancel=application.url)
        return data


class POST_TaskCreate(ToolMixin, MethodMixin, RedirectMixin, POST):
    "Create the BLAST task and start execution."

    fields = ()

    def handle(self, resource, request, application):
        self.check_quota(resource, request, application)
        self.inputs = self.parse_fields(request)
        self.preferences = dict()
        self.create_task()
        self.task.title = self.inputs.get('title')
        self.preferences['title'] = self.task.title
        self.task.data['parameters'] = dict()
        self.set_data()
        self.execute_task()
        self.set_preferences()
        self.redirect = application.get_url('task', self.task.iui)

    def set_data(self):
        raise NotImplementedError

    def set_db(self):
        db = self.inputs['db']
        self.task.data['parameters']['-db'] = ' '.join(db)
        self.preferences['db'] = db

    def set_query(self, query_type):
        query = self.inputs['query_file']
        if query:
            query = query['value']
        else:
            query = self.inputs['query_content']
        if not query:
            raise HTTP_BAD_REQUEST('no query specified')
        if query[0] != '>':   # Add FASTA header line
            query = ">query\n%s" % query
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
            self.preferences['db_gencode'] = db_gencode
        except KeyError:
            pass

    def set_query_gencode(self):
        try:
            query_gencode = self.inputs['query_gencode']
            self.task.data['parameters']['-query_gencode'] = query_gencode
            self.preferences['query_gencode'] = query_gencode
        except KeyError:
            pass

    def set_dust(self, default):
        try:
            dust = self.inputs['dust']
        except KeyError:
            dust = default
        self.task.data['parameters']['-dust'] = dust
        self.preferences['dust'] = dust

    def set_seg(self, default):
        try:
            seg = self.inputs['seg']
        except KeyError:
            seq = default
        self.task.data['parameters']['-seg'] = seg
        self.preferences['seg'] = seg

    def set_task_type(self, default):
        try:
            task_type = self.inputs['task_type']
        except KeyError:
            task_type = default
        self.task.data['parameters']['-task'] = task_type
        self.preferences['task_type'] = task_type

    def set_evalue(self):
        try:
            evalue = self.inputs['evalue']
            if evalue <= 0.0:
                raise HTTP_BAD_REQUEST('invalid E-value')
            self.task.data['parameters']['-evalue'] = evalue
            self.preferences['evalue'] = evalue
        except KeyError:
            pass

    def set_output_format(self):
        try:
            outfmt = self.inputs['outfmt']
            self.task.data['parameters']['-outfmt'] = outfmt
            self.preferences['outfmt'] = outfmt
        except KeyError:
            pass

    def set_num_descriptions(self):
        try:
            number = self.inputs['num_descriptions']
            if number < 0:
                raise HTTP_BAD_REQUEST('invalid # seq descriptions')
            self.task.data['parameters']['-num_descriptions'] = number
            self.preferences['num_descriptions'] = number
        except KeyError:
            pass

    def set_num_alignments(self):
        try:
            number = self.inputs['num_alignments']
            if number < 0:
                raise HTTP_BAD_REQUEST('invalid # seq alignments')
            self.task.data['parameters']['-num_alignments'] = number
            self.preferences['num_alignments'] = number
        except KeyError:
            pass

    def execute_task(self):
        self.task.create(self.login['name'])
        process = subprocess.Popen([configuration.PYTHON,
                                    configuration.EXECUTE_SCRIPT,
                                    self.task.iui])
        process.wait()                  # Only waits for daemonize to finish


class GET_BlastnCreate(GET_BlastCreate):
    "Blastn tool: nucleotide query against a nucleotide database."

    tool = 'blastn'
    database_type = 'nucleotide'

    fields = (StringField('title', title='Title', length=30,
                          descr='Descriptive title for the task.'),
              DbMultiSelectField('db', title='Database',
                                 required=True, check=False,
                                 descr='Check the nucleotide database(s)'
                                       ' to search.'),
              FileField('query_file', title='Query file',
                        descr='Upload file containing query nucleotide'
                              ' sequence(s) in FASTA format.'),
              TextField('query_content', title='Query',
                        descr='Query nucleotide sequence(s) in FASTA format.'
                              ' This data is used only if no file'
                              ' is specified in the field above.'),
              SelectField('dust', title='DUST filter',
                          options=['yes', 'no', '20 64 1'],
                          default='no', check=True,
                          descr='Filter out low-complexity regions'
                                ' from the query sequence.'),
              SelectField('task_type', title='Task type',
                          default='blastn',
                          options=[dict(value='blastn',
                                        title='blastn: traditional, requiring'
                                              ' an exact match of 11'),
                                   dict(value='blastn-short',
                                        title='blastn-short: optimized for'
                                              ' sequences < 50 bases'),
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
                           descr='Number of alignments to show in the output.'),
              CheckboxField('set_preferences', title='Set preferences',
                            default=False,
                            text='Set the above values to become your defaults'
                            ' for this tool.'))

    @property
    def descr(self):
        return '''BLAST search in a **nucleotide database** using
a **nucleotide query**. Executable version %s. For more information,
see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' \
    % configuration.BLAST_VERSION


class POST_BlastnCreate(POST_TaskCreate):
    "Create and start execution of a 'blastn' task."

    tool = 'blastn'

    fields = GET_BlastnCreate.fields

    def set_data(self):
        self.set_db()
        self.set_query('nucleotide')
        self.set_dust('no')
        self.set_task_type('blastn')
        self.set_evalue()
        self.set_output_format()
        self.set_num_descriptions()
        self.set_num_alignments()


class GET_BlastpCreate(GET_BlastCreate):
    "Blastp task: protein query against a protein database."

    tool = 'blastp'
    database_type = 'protein'

    fields = (StringField('title', title='Title', length=30,
                          descr='Descriptive title for the task.'),
              DbMultiSelectField('db', title='Database',
                                 required=True, check=False,
                                 descr='Check the protein database(s)'
                                       ' to search.'),
              FileField('query_file', title='Query file',
                        descr='Upload file containing query protein'
                              ' sequence(s) in FASTA format.'),
              TextField('query_content', title='Query',
                        descr='Query protein sequence(s) in FASTA format.'
                              ' This data is used only if no file'
                              ' is specified in the field above.'),
              SelectField('seg', title='SEG filter',
                          options=['yes', 'no', '12 2.2 2.5'],
                          default='no', check=True,
                          descr='Filter out low-complexity regions'
                                ' from the query sequence.'),
              SelectField('task_type', title='Task type',
                          default='blastp',
                          options=[dict(value='blastp',
                                        title='blastp: traditional, to'
                                              ' compare proteins'),
                                    dict(value='blastp-short',
                                         title='blastp-short: optimized for'
                                               ' sequences < 30 residues')],
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
                           descr='Number of alignments to show in the output.'),
              CheckboxField('set_preferences', title='Set preferences',
                            default=False,
                            text='Set the above values to become your'
                                 ' defaults for this tool.'))

    @property
    def descr(self):
        return '''BLAST search in a **protein database** using
a **protein query**. Executable version %s. For more information,
see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' \
    % configuration.BLAST_VERSION


class POST_BlastpCreate(POST_TaskCreate):
    "Create and start execution of a 'blastp' task."

    tool = 'blastp'

    fields = GET_BlastpCreate.fields

    def set_data(self):
        self.set_db()
        self.set_query('protein')
        self.set_task_type('blastp')
        self.set_seg('no')
        self.set_evalue()
        self.set_output_format()
        self.set_num_descriptions()
        self.set_num_alignments()


class GET_BlastxCreate(GET_BlastCreate):
    "Blastp task: translated nucleotide query against a protein database."

    tool = 'blastx'
    database_type = 'protein'

    fields = (StringField('title', title='Title', length=30,
                          descr='Descriptive title for the task.'),
              DbMultiSelectField('db', title='Database',
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
                          default='12 2.2 2.5', check=True,
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
                           descr='Number of alignments to show in the output.'),
              CheckboxField('set_preferences', title='Set preferences',
                            default=False,
                            text='Set the above values to become your'
                                 ' defaults for this tool.'))

    @property
    def descr(self):
        return '''BLAST search in a **protein database** using
a **translated nucleotide query**. Executable version %s. For more information,
see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' \
    % configuration.BLAST_VERSION


class POST_BlastxCreate(POST_TaskCreate):
    "Create and start execution of a 'blastx' task."

    tool = 'blastx'

    fields = GET_BlastxCreate.fields

    def set_data(self):
        self.set_db()
        self.set_query('nucleotide')
        self.set_query_gencode()
        self.set_seg('12 2.2 2.5')
        self.set_evalue()
        self.set_output_format()
        self.set_num_descriptions()
        self.set_num_alignments()


class GET_TblastnCreate(GET_BlastCreate):
    "Tblastn task: protein query against a translated nucleotide database."

    tool = 'tblastn'
    database_type = 'nucleotide'

    fields = (StringField('title', title='Title', length=30,
                          descr='Descriptive title for the task.'),
              DbMultiSelectField('db', title='Database',
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
                          default='12 2.2 2.5', check=True,
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
                           descr='Number of alignments to show in the output.'),
              CheckboxField('set_preferences', title='Set preferences',
                            default=False,
                            text='Set the above values to become your'
                                 ' defaults for this tool.'))

    @property
    def descr(self):
        return '''BLAST search in a **translated nucleotide database** using
a **protein query**. Executable version %s. For more information,
see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' \
    % configuration.BLAST_VERSION


class POST_TblastnCreate(POST_TaskCreate):
    "Create and start execution of a 'tblastn' task."

    tool = 'tblastn'

    fields = GET_TblastnCreate.fields

    def set_data(self):
        self.set_db()
        self.set_db_gencode()
        self.set_query('protein')
        self.set_seg('12 2.2 2.5')
        self.set_evalue()
        self.set_output_format()
        self.set_num_descriptions()
        self.set_num_alignments()


class GET_TblastxCreate(GET_BlastCreate):
    """Tblastx task: translated nucleotide query against
    a translated nucleotide database."""

    tool = 'tblastx'
    database_type = 'nucleotide'

    fields = (StringField('title', title='Title', length=30,
                          descr='Descriptive title for the task.'),
              DbMultiSelectField('db', title='Database',
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
                          default='12 2.2 2.5', check=True,
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
                           descr='Number of alignments to show in the output.'),
              CheckboxField('set_preferences', title='Set preferences',
                            default=False,
                            text='Set the above values to become your'
                                 ' defaults for this tool.'))

    @property
    def descr(self):
        return '''BLAST search in a **translated nucleotide database** using
a **translated nucleotide query**. Executable version %s. For more information,
see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).''' \
    % configuration.BLAST_VERSION


class POST_TblastxCreate(POST_TaskCreate):
    "Create and start execution of a 'tblastx' task."

    tool = 'tblastx'

    fields = GET_TblastxCreate.fields

    def set_data(self):
        self.set_db()
        self.set_db_gencode()
        self.set_query('nucleotide')
        self.set_query_gencode()
        self.set_seg('12 2.2 2.5')
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
        # Save the pid of the process doing the heavy work.
        task.pid = process.pid          # Implicit save
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
            task.status = configuration.FAILED # Implicit save.
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
    application.append(Resource('/blastn',
                                type='Tool blastn',
                                GET=GET_BlastnCreate(),
                                POST=POST_BlastnCreate()))
    application.append(Resource('/blastp',
                                type='Tool blastp',
                                GET=GET_BlastpCreate(),
                                POST=POST_BlastpCreate()))
    application.append(Resource('/blastx',
                                type='Tool blastx',
                                GET=GET_BlastxCreate(),
                                POST=POST_BlastxCreate()))
    application.append(Resource('/tblastn',
                                type='Tool tblastn',
                                GET=GET_TblastnCreate(),
                                POST=POST_TblastnCreate()))
    application.append(Resource('/tblastx',
                                type='Tool tblastx',
                                GET=GET_TblastxCreate(),
                                POST=POST_TblastxCreate()))
