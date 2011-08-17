""" Adhoc web resource.

BLAST web resources and tools.
"""

import os
import json
import subprocess

from .webresource import *


BLASTDB = os.path.join(configuration.DB_DIR, 'blast')
os.environ['BLASTDB'] = BLASTDB


def get_databases(type, userteams):
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
            if not teams.intersection(userteams): continue
        result.append(db)
    return result

BLASTN_TASK_TYPES = ['blastn', 'blastn-short', 'megablast', 'dc-megablast']
BLASTP_TASK_TYPES = ['blastp', 'blastp-short']

DUST_VALUES = ['yes', 'no', '20 64 1']
SEG_VALUES = ['yes', 'no', '12 2.2 2.5']

OUTPUT_FORMATS = [('0', 'Pairwise', 'text/plain'),
                  ('1', 'Query-anchored showing identities', 'text/plain'),
                  ('2', 'Query-anchored no identities', 'text/plain'),
                  ('3', 'Flat query-anchored, show identities', 'text/plain'),
                  ('4', 'Flat query-anchored, no identities', 'text/plain'),
                  ('5', 'XML Blast output', 'application/xml'),
                  ('6', 'Tab-separated values', 'text/tab-separated-values'),
                  ('7', 'Tab-separated values with comment lines',
                   'text/tab-separated-values'),
                  ('8', 'Text ASN.1', 'text/plain'),
                  ('10', 'Comma-separated values', 'text/csv'),
                  ('11', 'BLAST archive format (ASN.1)', 'text/plain')]

# 2011-07-14: http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi
GENETIC_CODES = [('1', 'Standard'),
                 ('2', 'Vertebrate Mitochondrial'),
                 ('3', 'Yeast Mitochondrial'),
                 ('4', 'Mold Mitochondrial; Protozoan Mitochondrial; Coelenterate Mitochondrial; Mycoplasma; Spiroplasma'),
                 ('5', 'Invertebrate Mitochondrial'),
                 ('6', 'Ciliate Nuclear; Dasycladacean Nuclear; Hexamita Nuclear'),
                 ('9', 'Echinoderm Mitochondrial; Flatworm Mitochondrial'),
                 ('10', 'Euplotid Nuclear'),
                 ('11', 'Bacterial and Plant Plastid'),
                 ('12', 'Alternative Yeast Nuclear'),
                 ('13', 'Ascidian Mitochondrial'),
                 ('14', 'Alternative Flatworm Mitochondrial'),
                 ('15', 'Blepharisma Macronuclear'),
                 ('16', 'Chlorophycean Mitochondrial'),
                 ('21', 'Trematode Mitochondrial'),
                 ('22', 'Scenedesmus obliquus Mitochondrial'),
                 ('23', 'Thraustochytrium Mitochondrial')]


class BlastCreate(WebResource):
    "Generic BLAST search task creator."

    tool = None
    description = None

    def row_execute(self):
        return TR(TH(),
                  TD(INPUT(type='submit', value='Execute task'), colspan=2))

    def row_spacer(self):
        return TR(TH(style='height:1em;'))

    def row_title(self):
        return TR(TH('Title'),
                  TD(),
                  TD(INPUT(type='text', name='title')))

    def row_db(self, type):
        rows = [TR(TH('Include'),
                   TH('Title'),
                   TH('File'),
                   TH('# seqs'),
                   TH('Size'),
                   TH('Updated'))]
        for db in get_databases(type, self.user['teams']):
            rows.append(TR(TD(INPUT(type='checkbox',
                                    name='db',
                                    value=db['filename']),
                              klass='clean'),
                           TD(db['title']),
                           TD(db['filename']),
                           TD(db['number'], klass='number'),
                           TD(db['size'], klass='number'),
                           TD(db['updated'])))
        return TR(TH('Database'),
                  TD(REQUIRED),
                  TD(TABLE(klass='list', *rows)))

    def row_db_gencode(self):
        return TR(TH('Database genetic code'),
                  TD(),
                  TD(SELECT(name='db_gencode',
                            *[OPTION(r[1], value=r[0])
                              for r in GENETIC_CODES])))

    def row_query(self, type):
        return TR(TH('Query'),
                  TD(REQUIRED),
                  TD(TABLE(TR(TD(I("Paste %s sequence in FASTA format:" %type)),
                              TD(I('Or upload FASTA file:'))),
                           TR(TD(TEXTAREA(name='query', cols=60, rows=8),
                                 rowspan=2),
                              TD(INPUT(type='file', name='query_file'))),
                           TR(TD(INPUT(type='checkbox', checked=True,
                                       name='query_check', value='true'),
                                 ' Check query content.')))))

    def row_task_type(self, task_types):
        return TR(TH('Task type'),
                  TD(REQUIRED),
                  TD(SELECT(name='task_type',
                            *[OPTION(t) for t in task_types])))

    def row_query_gencode(self):
        return TR(TH('Query genetic code'),
                  TD(),
                  TD(SELECT(name='query_gencode',
                            *[OPTION(r[1], value=r[0])
                              for r in GENETIC_CODES])))

    def row_evalue(self):
        return TR(TH('E-value'),
                  TD(),
                  TD(INPUT(type='text', name='evalue', value='10')))

    def row_dust(self, default=None):
        return TR(TH('DUST filter'),
                  TD(),
                  TD(SELECT(name='dust', 
                            *[OPTION(d, selected=(d==default) or None)
                              for d in DUST_VALUES])))

    def row_seg(self, default=None):
        return TR(TH('SEG filter'),
                  TD(),
                  TD(SELECT(name='seg',
                            *[OPTION(d, selected=(d==default) or None)
                              for d in SEG_VALUES])))

    def row_output_format(self):
        return TR(TH('Output format'),
                  TD(),
                  TD(SELECT(name='outfmt', *[OPTION(f[1], value=f[0])
                                             for f in OUTPUT_FORMATS])))

    def row_num_descriptions(self):
        return TR(TH('# db seq descriptions'),
                  TD(),
                  TD(INPUT(type='text', name='num_descriptions', value='500')))

    def row_num_alignments(self):
        return TR(TH('# alignments'),
                  TD(),
                  TD(INPUT(type='text', name='num_alignments', value='250')))

    def output(self, rows, response):
        html = HtmlRepresentation(self, self.tool)
        html.abstract = markdown.markdown(self.description,
                                          output_format='html4')
        html.append(FORM(TABLE(klass='input', *rows),
                         enctype='multipart/form-data',
                         method='POST',
                         action=configuration.get_url(self.tool)))
        html.write(response)

    def create_task(self):
        from .task import Task
        self.task = Task(self.cnx)
        self.task.tool = self.tool
        self.task.title = self.get_cgi_value('title')
        self.task.data['parameters'] = dict()

    @property
    def parameters(self):
        return self.task.data['parameters']

    def set_db(self, type):
        databases = get_databases(type, self.user['teams'])
        result = []
        for filename in self.request.cgi_fields.getlist('db'):
            for db in databases:
                if filename == db['filename']:
                    break
            else:
                raise HTTP_BAD_REQUEST("invalid 'db' value '%s'" % filename)
            result.append(filename)
        if not result:
            raise HTTP_BAD_REQUEST("no 'db' value specified")
        self.parameters['-db'] = ' '.join(result)

    def set_db_gencode(self):
        gencode = self.get_cgi_value('db_gencode')
        if not gencode: return
        for code, descr in GENETIC_CODES:
            if code == gencode:
                break
        else:
            raise HTTP_BAD_REQUEST("invalid 'db_gencode' value")
        self.parameters['-db_gencode'] = gencode

    def set_query(self, type):
        try:
            query_file = self.request.cgi_fields['query_file'].file
            if not query_file: raise KeyError
            query = query_file.read().strip()
            if not query: raise KeyError
        except KeyError:
            query = self.get_cgi_value('query', required=True)
        if not query:
            raise HTTP_BAD_REQUEST('query is empty')
        # Add FASTA header line if not present
        if query[0] != '>':
            query = '>query\n' + query
        if configuration.to_bool(self.get_cgi_value('query_check')):
            characters = set()
            for line in query.split('\n'):
                if line[0] == '>': continue
                for c in line.strip():
                    characters.add(c.upper())
            if type == 'protein':
                if not characters.difference('ACTG'):
                    raise HTTP_BAD_REQUEST('query appears to be nucleotide')
            elif type == 'nucleotide':
                if characters.difference('ACTGX'):
                    raise HTTP_BAD_REQUEST('query appears to be protein')
        self.task.data['query'] = query

    def set_query_gencode(self):
        gencode = self.get_cgi_value('query_gencode')
        if not gencode: return
        for code, descr in GENETIC_CODES:
            if code == gencode:
                break
        else:
            raise HTTP_BAD_REQUEST("invalid 'query_gencode' value")
        self.parameters['-query_gencode'] = gencode

    def set_task_type(self, task_types):
        task_type = self.get_cgi_value('task_type', required=True)
        for tt in task_types:
            if tt == task_type:
                break
        else:
            raise HTTP_BAD_REQUEST("invalid 'task_type' value")
        self.parameters['-task'] = task_type

    def set_evalue(self):
        evalue = self.get_cgi_value('evalue')
        if not evalue: return
        try:
            evalue = float(evalue)
            if evalue <= 0.0: raise ValueError
        except (TypeError, ValueError):
            raise HTTP_BAD_REQUEST("invalid 'evalue' value")
        self.parameters['-evalue'] = evalue

    def set_dust(self):
        dust = self.get_cgi_value('dust')
        if not dust: return
        if not dust in DUST_VALUES:
            raise HTTP_BAD_REQUEST("invalid 'dust' value")
        self.parameters['-dust'] = dust

    def set_seg(self):
        seg = self.get_cgi_value('seg')
        if not seg: return
        if not seg in SEG_VALUES:
            raise HTTP_BAD_REQUEST("invalid 'seg' value")
        self.parameters['-seg'] = seg

    def set_outfmt(self):
        outfmt = self.get_cgi_value('outfmt')
        if outfmt:
            if not outfmt in set([f[0] for f in OUTPUT_FORMATS]):
                raise HTTP_BAD_REQUEST("invalid 'outfmt' value")
        else:
            outfmt = '0'
        self.parameters['-outfmt'] = outfmt

    def set_num_descriptions(self):
        num = self.get_cgi_value('num_descriptions')
        if not num: return
        try:
            num = int(num)
            if num < 0: raise ValueError
        except (TypeError, ValueError):
            raise HTTP_BAD_REQUEST("invalid 'num_descriptions' value")
        self.parameters['-num_descriptions'] = num

    def set_num_alignments(self):
        num = self.get_cgi_value('num_alignments')
        if not num: return
        try:
            num = int(num)
            if num < 0: raise ValueError
        except (TypeError, ValueError):
            raise HTTP_BAD_REQUEST("invalid 'num_alignments' value")
        self.parameters['-num_alignments'] = num

    def execute_task(self):
        self.task.create(self.user['id'])
        process = subprocess.Popen([configuration.PYTHON,
                                    configuration.TASK_SCRIPT,
                                    self.task.iui])
        process.wait()
        raise HTTP_SEE_OTHER(Location=self.task.get_url())


class BlastnCreate(BlastCreate):
    "Create a blastn search task."

    tool = 'blastn'
    description = \
'''Search in a **nucleotide database** using a **nucleotide query**. Version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).
''' % configuration.BLAST_VERSION

    def GET(self, request, response):
        rows = [self.row_execute(),
                self.row_spacer(),
                self.row_title(),
                self.row_db('nucleotide'),
                self.row_query('nucleotide'),
                self.row_task_type(BLASTN_TASK_TYPES),
                self.row_evalue(),
                self.row_dust(default='20 64 1'),
                self.row_output_format(),
                self.row_num_descriptions(),
                self.row_num_alignments(),
                self.row_spacer(),
                self.row_execute()]
        self.output(rows, response)

    def POST(self, request, response):
        self.check_write()
        self.create_task()
        self.set_db('nucleotide')
        self.set_query('nucleotide')
        self.set_task_type(BLASTN_TASK_TYPES)
        self.set_evalue()
        self.set_dust()
        self.set_outfmt()
        self.set_num_descriptions()
        self.set_num_alignments()
        self.execute_task()


class BlastpCreate(BlastCreate):
    "Create a blastp search task."

    tool = 'blastp'
    description = \
'''Search in a **protein database** using a **protein query**. Version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).
''' % configuration.BLAST_VERSION

    def GET(self, request, response):
        rows = [self.row_execute(),
                self.row_spacer(),
                self.row_title(),
                self.row_db('protein'),
                self.row_query('protein'),
                self.row_task_type(BLASTP_TASK_TYPES),
                self.row_evalue(),
                self.row_seg(),
                self.row_output_format(),
                self.row_num_descriptions(),
                self.row_num_alignments(),
                self.row_spacer(),
                self.row_execute()]
        self.output(rows, response)

    def POST(self, request, response):
        self.check_write()
        self.create_task()
        self.set_db('protein')
        self.set_query('protein')
        self.set_task_type(BLASTP_TASK_TYPES)
        self.set_evalue()
        self.set_seg()
        self.set_outfmt()
        self.set_num_descriptions()
        self.set_num_alignments()
        self.execute_task()


class BlastxCreate(BlastCreate):
    "Create a blastx search task."

    tool = 'blastx'
    description = \
'''Search in a **protein database** using a **translated nucleotide query**. Version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).
''' % configuration.BLAST_VERSION

    def GET(self, request, response):
        rows = [self.row_execute(),
                self.row_spacer(),
                self.row_title(),
                self.row_db('protein'),
                self.row_query('nucleotide'),
                self.row_query_gencode(),
                self.row_evalue(),
                self.row_seg(default='12 2.2 2.5'),
                self.row_output_format(),
                self.row_num_descriptions(),
                self.row_num_alignments(),
                self.row_spacer(),
                self.row_execute()]
        self.output(rows, response)

    def POST(self, request, response):
        self.check_write()
        self.create_task()
        self.set_db('protein')
        self.set_query('nucleotide')
        self.set_query_gencode()
        self.set_evalue()
        self.set_seg()
        self.set_outfmt()
        self.set_num_descriptions()
        self.set_num_alignments()
        self.execute_task()


class TblastnCreate(BlastCreate):
    "Create a tblastn search task."

    tool = 'tblastn'
    description = \
'''Search in a **translated nucleotide database** using a **protein query**. Version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).
''' % configuration.BLAST_VERSION

    def GET(self, request, response):
        rows = [self.row_execute(),
                self.row_spacer(),
                self.row_title(),
                self.row_db('nucleotide'),
                self.row_db_gencode(),
                self.row_query('protein'),
                self.row_evalue(),
                self.row_seg(default='12 2.2 2.5'),
                self.row_output_format(),
                self.row_num_descriptions(),
                self.row_num_alignments(),
                self.row_spacer(),
                self.row_execute()]
        self.output(rows, response)

    def POST(self, request, response):
        self.check_write()
        self.create_task()
        self.set_db('nucleotide')
        self.set_db_gencode()
        self.set_query('protein')
        self.set_evalue()
        self.set_seg()
        self.set_outfmt()
        self.set_num_descriptions()
        self.set_num_alignments()
        self.execute_task()


class TblastxCreate(BlastCreate):
    "Create a tblastx search task."

    tool = 'tblastx'
    description = \
'''Search in a **translated nucleotide database** using a **translated nucleotide query**. Version %s.

For more information, see the [BLAST Help at NCBI](http://www.ncbi.nlm.nih.gov/books/NBK1762/).
''' % configuration.BLAST_VERSION

    def GET(self, request, response):
        rows = [self.row_execute(),
                self.row_spacer(),
                self.row_title(),
                self.row_db('nucleotide'),
                self.row_db_gencode(),
                self.row_query('nucleotide'),
                self.row_query_gencode(),
                self.row_evalue(),
                self.row_seg(default='12 2.2 2.5'),
                self.row_output_format(),
                self.row_num_descriptions(),
                self.row_num_alignments(),
                self.row_spacer(),
                self.row_execute()]
        self.output(rows, response)

    def POST(self, request, response):
        self.check_write()
        self.create_task()
        self.set_db('nucleotide')
        self.set_db_gencode()
        self.set_query('nucleotide')
        self.set_query_gencode()
        self.set_evalue()
        self.set_seg()
        self.set_outfmt()
        self.set_num_descriptions()
        self.set_num_alignments()
        self.execute_task()


class BlastTool(object):
    "General BLAST tool."

    def __init__(self, tool):
        self.tool = tool

    def __call__(self, task):
        assert task.tool == self.tool
        assert task.status == 'executing'
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
        for code, descr, mimetype in OUTPUT_FORMATS:
            if code == outfmt:
                task.data['output_content_type'] = mimetype
                break
        else:
            task.data['output_content_type'] = 'text/plain'
        task.data['error'] = stderr
        if process.returncode > 0:
            task.status = 'failed'
        elif process.returncode < 0:
            task.status = 'killed'
        else:
            task.status = 'finished'


def setup(application):
    "Setup the web application interface."
    application.add_dispatcher('template:/blastn', BlastnCreate)
    application.add_dispatcher('template:/blastp', BlastpCreate)
    application.add_dispatcher('template:/blastx', BlastxCreate)
    application.add_dispatcher('template:/tblastn', TblastnCreate)
    application.add_dispatcher('template:/tblastx', TblastxCreate)

# Add the above tools to the configuration.
configuration.add_tool(name='blastn',
                       function=BlastTool('blastn'),
                       description=BlastnCreate.description,
                       version=configuration.BLAST_VERSION)
configuration.add_tool(name='blastp',
                       function=BlastTool('blastp'),
                       description=BlastpCreate.description,
                       version=configuration.BLAST_VERSION)
configuration.add_tool(name='blastx',
                       function=BlastTool('blastx'),
                       description=BlastxCreate.description,
                       version=configuration.BLAST_VERSION)
configuration.add_tool(name='tblastn',
                       function=BlastTool('tblastn'),
                       description=TblastnCreate.description,
                       version=configuration.BLAST_VERSION)
configuration.add_tool(name='tblastx',
                       function=BlastTool('tblastx'),
                       description=TblastxCreate.description,
                       version=configuration.BLAST_VERSION)
