"""
Template Rendering System for Advanced Reporting

This module provides comprehensive template rendering capabilities for generating
dynamic reports with flexible layouts, data binding, and component composition.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from jinja2.exceptions import TemplateError, TemplateNotFound
from markupsafe import Markup

logger = logging.getLogger(__name__)


class TemplateFormat(Enum):
    """Supported template formats"""
    HTML = "html"
    JSON = "json"
    MARKDOWN = "md"
    XML = "xml"
    TEXT = "txt"


class ComponentType(Enum):
    """Types of reusable report components"""
    CHART = "chart"
    TABLE = "table"
    METRIC = "metric"
    SUMMARY = "summary"
    HEADER = "header"
    FOOTER = "footer"
    SECTION = "section"


@dataclass
class TemplateMetadata:
    """Metadata for report templates"""
    name: str
    version: str
    description: str
    format: TemplateFormat
    author: str
    created_date: datetime
    modified_date: datetime
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderContext:
    """Context for template rendering"""
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Callable] = field(default_factory=dict)
    globals: Dict[str, Any] = field(default_factory=dict)
    components: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentDefinition:
    """Definition of a reusable report component"""
    name: str
    type: ComponentType
    template: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    css_classes: List[str] = field(default_factory=list)
    javascript: Optional[str] = None


class TemplateRenderer:
    """
    Advanced template rendering engine with support for multiple formats,
    component composition, and dynamic data binding.
    """
    
    def __init__(self, template_dir: str = "src/resources/templates"):
        """
        Initialize the template renderer.
        
        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self._register_custom_filters()
        
        # Template cache
        self._template_cache: Dict[str, Template] = {}
        self._metadata_cache: Dict[str, TemplateMetadata] = {}
        
        logger.info(f"TemplateRenderer initialized with template directory: {self.template_dir}")
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters for report generation"""
        
        def format_number(value: Union[int, float], decimals: int = 2) -> str:
            """Format numbers with specified decimal places"""
            if isinstance(value, (int, float)):
                return f"{value:,.{decimals}f}"
            return str(value)
        
        def format_percentage(value: Union[int, float], decimals: int = 1) -> str:
            """Format values as percentages"""
            if isinstance(value, (int, float)):
                return f"{value:.{decimals}f}%"
            return str(value)
        
        def format_duration(seconds: Union[int, float]) -> str:
            """Format duration in seconds to human-readable format"""
            if not isinstance(seconds, (int, float)):
                return str(seconds)
            
            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                minutes = seconds / 60
                return f"{minutes:.1f}m"
            else:
                hours = seconds / 3600
                return f"{hours:.1f}h"
        
        def format_bytes(bytes_value: Union[int, float]) -> str:
            """Format byte values to human-readable format"""
            if not isinstance(bytes_value, (int, float)):
                return str(bytes_value)
            
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"
        
        def truncate_text(text: str, length: int = 100, suffix: str = "...") -> str:
            """Truncate text to specified length"""
            if len(text) <= length:
                return text
            return text[:length - len(suffix)] + suffix
        
        def highlight_keywords(text: str, keywords: List[str], 
                             css_class: str = "highlight") -> Markup:
            """Highlight keywords in text"""
            if not keywords:
                return Markup(text)
            
            pattern = '|'.join(re.escape(keyword) for keyword in keywords)
            highlighted = re.sub(
                f'({pattern})', 
                f'<span class="{css_class}">\\1</span>', 
                text, 
                flags=re.IGNORECASE
            )
            return Markup(highlighted)
        
        # Register filters
        self.env.filters['format_number'] = format_number
        self.env.filters['format_percentage'] = format_percentage
        self.env.filters['format_duration'] = format_duration
        self.env.filters['format_bytes'] = format_bytes
        self.env.filters['truncate_text'] = truncate_text
        self.env.filters['highlight_keywords'] = highlight_keywords
    
    def load_template(self, template_name: str) -> Template:
        """
        Load a template by name with caching.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Loaded Jinja2 template
            
        Raises:
            TemplateNotFound: If template file doesn't exist
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        
        try:
            template = self.env.get_template(template_name)
            self._template_cache[template_name] = template
            logger.debug(f"Loaded template: {template_name}")
            return template
        except TemplateNotFound as e:
            logger.error(f"Template not found: {template_name}")
            raise e
    
    def load_template_metadata(self, template_name: str) -> Optional[TemplateMetadata]:
        """
        Load template metadata from accompanying metadata file.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Template metadata if available, None otherwise
        """
        if template_name in self._metadata_cache:
            return self._metadata_cache[template_name]
        
        # Look for metadata file (template_name.meta.yaml)
        base_name = Path(template_name).stem
        metadata_file = self.template_dir / f"{base_name}.meta.yaml"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_dict = yaml.safe_load(f)
            
            metadata = TemplateMetadata(
                name=metadata_dict.get('name', base_name),
                version=metadata_dict.get('version', '1.0.0'),
                description=metadata_dict.get('description', ''),
                format=TemplateFormat(metadata_dict.get('format', 'html')),
                author=metadata_dict.get('author', 'Unknown'),
                created_date=datetime.fromisoformat(
                    metadata_dict.get('created_date', datetime.now().isoformat())
                ),
                modified_date=datetime.fromisoformat(
                    metadata_dict.get('modified_date', datetime.now().isoformat())
                ),
                tags=metadata_dict.get('tags', []),
                dependencies=metadata_dict.get('dependencies', []),
                parameters=metadata_dict.get('parameters', {})
            )
            
            self._metadata_cache[template_name] = metadata
            logger.debug(f"Loaded metadata for template: {template_name}")
            return metadata
            
        except Exception as e:
            logger.warning(f"Failed to load metadata for template {template_name}: {e}")
            return None
    
    def render_template(self, template_name: str, context: RenderContext) -> str:
        """
        Render a template with the provided context.
        
        Args:
            template_name: Name of the template to render
            context: Rendering context with data and configuration
            
        Returns:
            Rendered template as string
            
        Raises:
            TemplateError: If template rendering fails
        """
        try:
            template = self.load_template(template_name)
            
            # Prepare rendering context
            render_context = {
                **context.data,
                **context.globals,
                'metadata': context.metadata,
                'components': context.components,
                'now': datetime.now(),
                'template_name': template_name
            }
            
            # Add custom filters to context if provided
            if context.filters:
                for filter_name, filter_func in context.filters.items():
                    self.env.filters[filter_name] = filter_func
            
            # Render template
            rendered = template.render(**render_context)
            
            logger.debug(f"Successfully rendered template: {template_name}")
            return rendered
            
        except TemplateError as e:
            logger.error(f"Template rendering error for {template_name}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error rendering template {template_name}: {e}")
            raise TemplateError(f"Failed to render template {template_name}: {e}")
    
    def render_string(self, template_string: str, context: RenderContext) -> str:
        """
        Render a template from string content.
        
        Args:
            template_string: Template content as string
            context: Rendering context with data and configuration
            
        Returns:
            Rendered template as string
        """
        try:
            template = self.env.from_string(template_string)
            
            render_context = {
                **context.data,
                **context.globals,
                'metadata': context.metadata,
                'components': context.components,
                'now': datetime.now()
            }
            
            return template.render(**render_context)
            
        except TemplateError as e:
            logger.error(f"String template rendering error: {e}")
            raise e
    
    def validate_template(self, template_name: str) -> Dict[str, Any]:
        """
        Validate a template for syntax errors and dependencies.
        
        Args:
            template_name: Name of the template to validate
            
        Returns:
            Validation results with errors and warnings
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'dependencies': []
        }
        
        try:
            # Load and parse template
            template = self.load_template(template_name)
            
            # Check for undefined variables (basic check)
            # This is a simplified validation - in production, you might want more sophisticated checks
            template_source = template.source
            
            # Extract template dependencies (includes, extends, imports)
            include_pattern = r'{%\s*include\s+["\']([^"\']+)["\']'
            extend_pattern = r'{%\s*extends\s+["\']([^"\']+)["\']'
            import_pattern = r'{%\s*import\s+["\']([^"\']+)["\']'
            
            includes = re.findall(include_pattern, template_source)
            extends = re.findall(extend_pattern, template_source)
            imports = re.findall(import_pattern, template_source)
            
            dependencies = list(set(includes + extends + imports))
            validation_result['dependencies'] = dependencies
            
            # Check if dependencies exist
            for dep in dependencies:
                dep_path = self.template_dir / dep
                if not dep_path.exists():
                    validation_result['errors'].append(f"Dependency not found: {dep}")
                    validation_result['valid'] = False
            
            # Load metadata and check compatibility
            metadata = self.load_template_metadata(template_name)
            if metadata:
                for dep in metadata.dependencies:
                    if dep not in dependencies:
                        validation_result['warnings'].append(
                            f"Metadata dependency not found in template: {dep}"
                        )
            
            logger.debug(f"Template validation completed for: {template_name}")
            
        except TemplateError as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Template syntax error: {e}")
        except Exception as e:
      )xtme, conteplate_natemr_template(endeer.rself.rendern etur  r
      
                )     }
ame
       template_nte':    'templa           ow(),
  time.nd_at': dateenerate        'g
        ={tadata  me    ,
       {}mponents oronents=co comp          
 data,data=          Context(
  Renderntext =     co"""
       ML
     eport HTRendered r        s:
       Return
             
    nent dataonal compo Optis:   component        data
 eport  data: R          e
  us template tome of thee_name: Naat    templ       Args:
      
   
        nents.te and compo templa usingort rep complete   Render a     
    """:
    ne) -> str] = Nony]t[str, Aional[Dics: Opt   component                  Any], 
Dict[str, ta: e: str, dalate_nam(self, temper_reportdef rend
    n info
    urret        
     ation
   = valid] idation'   info['valme)
     (nalatete_tempderer.valida= self.ren validation 
       ion resultsvalidatdd  A
        #    })
                ameters
tadata.parers': me   'paramet      es,
       pendencitadata.dedencies': me  'depen            ags,
  data.ts': meta 'tag            
   thor,a.au metadatauthor':           '  e,
   mat.valuata.format': metad     'for       tion,
    crip.des: metadataion'riptdesc  '        
      ersion,ata.vtadn': me 'versio               ate({
o.updinf       ta:
     metada     if a(name)
   ate_metadatd_temploa.renderer.lata = selfad    meta
    metadat    # Add          
 
         }ime)
 tat().st_mtath.sate_pp(templfromtimestametime.': datified    'mod
        ze,.st_sit()_path.staemplatee': t      'siz     
 e_path),tr(templatpath': s     '  
     ame': name,  'n       fo = {
        in       
   
 urn None ret         ists():
  .expathot template_ if nme
       ate_dir / natemplf. selplate_path =   tem"""
           
  aryondictin informatiote      Templa:
       urns      Ret
       
       plate nameTem   name:            Args:
    
      
    a template.n about formatio innsiveehecomprt         Ge""

        "y]]:r, Anl[Dict[stnatr) -> Optiome: s nafo(self,_inateget_templ  
    def False
     return    }")
      {ee {name}: eate templat to cror(f"Failedrr logger.e         :
  ption as eexcept Exce
                n True
           retur
     ")}{namee: ted templat(f"Creaogger.info  l
                     e=False)
 ylult_flow_stdefa f, tadata_dict,ump(me     yaml.d        
    f:'utf-8') ascoding=', enata_path, 'w(metad open     with 
       
           }     
       .parameters: metadatarameters'  'pa            s,
  denciea.dependats': metancie 'depende           ,
    tadata.tags': metags           'at(),
     rmofo.isdified_datemetadata.mo: _date'fiedodi'm           t(),
     ate.isoformaa.created_d metadat_date': 'created              or,
 ta.auth: metadathor'     'au
           t.value,a.formatadatormat': me     'f           cription,
adata.deset miption':scr       'de       version,
   metadata.':    'version            me,
a.nae': metadat   'nam        {
     _dict = metadata                 
       aml"
me}.meta.ye_naasdir / f"{blate_elf.tempta_path = s metada         stem
  h(name)._name = Pat     baseile
       data fite metaWr       #     
             
e(content)     f.writ     
       f:'utf-8') asg='w', encodin, late_pathen(tempwith op          me
  r / naplate_dielf.teme_path = smplat     te       plate file
 Write tem  #             try:
"
        ""    erwise
  False othlly,ed successfuatre  True if c       s:
   turn
        Re          metadata
  : Template  metadata       
    tentplate cont: Temnten co          e
 nam Template  name:
             Args:
              etadata.
 with mlateew temp Create a n
          """  l:
   ata) -> booadplateMetTema: adat, met strtent:str, con, name: plate(selff create_tem   de
    
 ized")y initialbrarateLipl"Temr.info(logge       
        brary()
 nentLi = Component_librarycompo       self.te_dir))
 emplaerer(str(tlateRendr = Tempereself.rendr)
        e_dimplatr = Path(tee_diplatf.tem  sel          """
    mplates
g teininntaory co Directr:plate_di    tem        gs:
   Ar 
     
       te library.e templatialize th      Ini  """
  "):
      s/templatessource "src/restr =_dir: atetempl_(self, _init_def _    
        """
lates.
empreport tversioning d g anmanaginibrary for "
    L""  :
  braryemplateLiss T

clatext)
_conomponentate, cnt.templnepoing(comrender_strer.urn render      ret  
    )
       nents
     mpoontext.co=ccomponents           s,
 ntext.global  globals=co        ers,
  xt.filtilters=conte         ftadata,
   ntext.medata=co meta          meters},
 parant.*componext.data, *{**conte   data=      t(
   rContex Rendetext =nent_conpo  com    
  xtconters with rametent paerge compone        # M       
ame}")
 ound: {nt fno"Component flueError(    raise Va
        t:ponencomnot     if 
    e)onent(namomp= self.get_ct    componen"
           ""nd
  ent not fouf componror: IueEr  Val
          ses: Rai
                   onent HTML
d compRendere           s:
 rn     Retu     
   ext
       g contnderintext: Re    cone
        nstancenderer iemplate renderer: T    r    
    menaent Compon     name: gs:
         Ar
          t.
    ontexprovided cnt with the  a componeRender       
 ""     "   r:
> stContext) -ert: Rend      contex          , 
        ererplateRendnderer: Temme: str, re nant(self,nerender_compof 
    de
     x.name)x:key=lambda ponents, n sorted(cometur    r       
 ]
    t_type == componenc.typenents if  in compo= [c for cmponents           cotype:
  ent_  if compon 
            s())
 s.valuenentself._compo= list(s omponent   c     "
   ""  
   itionsnt definmponest of co   Li         s:
urn        Ret     
er
       e filtonent typtional compt_type: Opomponen       c
     Args:      
       
    type.d byiltereally fionents, optcomponailable t av      Lis"""
     
     ion]:Definitt[Componente) -> Lis] = NontTypenal[Componentype: Optiocomponent_, s(selft_component   def lis 
 name)
   et(onents.g_competurn self.
        r     """   otherwise
ne und, No if foition definent   Compon:
              Returns             
t name
  nenmpo name: Co            Args:
      
         y name.
inition bt defmponen co      Get a""
  
        "ion]:finitntDeneional[Compo> Optstr) -lf, name: t(seenf get_componde    
    }")
}: {eent_file {componmponent fromo load co"Failed tr.error(f  logge     
         tion as e:xcept Excep   e                  
     
  }")mecomponent.naomponent: {Loaded cf".debug(er        logg   nent
     me] = compoent.naents[componcomponelf._     s       
                   )
              ')
   avascriptdata.get('j=component_javascript             ]),
       _classes', [et('cssnt_data.gses=compone css_clas             ]),
      ncies', [depende.get('onent_datamp=coesependenci    d            
    ,{})ameters', arget('pponent_data.ameters=com    par               
 '],a['templatent_datomponeemplate=c        t      ,
      e'])data['typcomponent_tType(mponen     type=Co               'name'],
data[omponent_ame=c        n   
         inition(omponentDefnent = C      compo                   

       e_load(f)afa = yaml.smponent_dat    co               as f:
  8')'utf-ding= encot_file, 'r',nenompoopen(c    with             ry:
     t):
       "*.yaml"s_dir.glob(mponentf.co_file in selntompone for c    ""
   "irectorycomponents dns from the itioent defin compon"""Load      
  ts(self):_componen def _load     
s")
  componentmponents)} ._coen(self {lalized withibrary initiComponentLer.info(f"   logg     
     nts()
   componeload_     self._= {}
   n] Definitioomponent, Ct[strDicomponents:   self._c
      e)
        st_ok=TruexiTrue, parents=kdir(nts_dir.mlf.compone     se
   ts_dir)th(componen = Pamponents_dirf.co        sel"""
    
    onsiti definng componentnictory contaiDirer: _dinentscompo            :
rgs     A
          
  library.he componentnitialize t
        I"""       s"):
 es/componentrc"src/resour: str = ponents_di_(self, comit___inef     
    d """
   omponents.
report ce  reusablgingnaary for ma  Libr"""
      ntLibrary:
s Compone
clas

eared")caches cl"Template nfo(er.i     logglear()
   ta_cache.cdataelf._me  s)
      clear(late_cache.elf._temp       ss"""
 he cactadatad mete anClear templa    """f):
    he(sel clear_cac  
    def
  name'])a x: x['ambds, key=lemplateed(teturn sort    r        
info)
    nd(template_mplates.appe   te            
      
            })s
       adata.tag: met 'tags'           r,
        autho metadata.  'author':               e,
   format.valutadata.ormat': me 'f                tion,
   ipescr metadata.dscription':        'de     on,
       tadata.versi': me 'version                ate({
   nfo.updplate_iem     t          
 ta:tada       if mee)
     _file.namplateata(temtad_template_me = self.load  metadata       lable
   vaietadata if a # Load m
                
                }  
 time)t_m().sile.stat_fp(templateamstime.fromtimed': datet  'modifie     
         ().st_size,te_file.statmpla te':      'size          ate_file),
str(templth':      'pa       
    file.name,emplate_me': t         'na  {
     _info = mplate          te   
      tinue
             con
        .yaml'):swith('.metae.endamate_file.n   if templ      "):
   lob("*.htmglmplate_dir. in self.telate_file temp  for
          s = []
    telatemp     "
   ""      ies
  ctionartion dite informalat of temp      Lis:
           Returns     
   
   a.r metadatith thei templates wlableavaiall    List """
     
        str, Any]]: List[Dict[ ->ates(self)templ  def list_t
    
  ion_resulturn validat       re     
 )
   : {e}"orn errValidatio].append(f"s'errort['esuldation_r vali     
       = False'valid']esult[n_rvalidatio      