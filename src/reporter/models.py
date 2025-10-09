from pydantic import BaseModel, Field, field_validator
from enum import Enum 
from typing import Optional, List, Union

class NIHAgency(Enum): 
    CLC = "CLC"
    CSR = "CSR"
    CIT = "CIT"
    FIC = "FIC"
    NCATS = "NCATS"
    NCCIH = "NCCIH"
    NCI = "NCI"
    NCRR =  "NCRR"
    NEI = "NEI"
    NHGRI = "NHGRI"
    NHLBI = "NHLBI"
    NIA = "NIA"
    NIAAA = "NIAAA"
    NIAID = "NIAID" 
    NIAMS = "NIAMS"
    NIBIB = "NIBIB"
    NICHD = "NICHD"
    NIDA = "NIDA"
    NIDCD = "NIDCD"
    NIDCR = "NIDCR"
    NIDDK = "NIDDK"
    NIEHS = "NIEHS"
    NIGMS = "NIGMS"
    NIH = "NIH"
    NIMH = "NIMH"
    NIMHD = "NIMHD"
    NINDS = "NINDS"
    NINR = "NINR"
    NLM = "NLM"
    OD = "OD"

    @classmethod
    def get_full_name(cls, code: str) -> str:
        """Get the full name of an agency from its code"""
        full_names = {
            "CLC": "Clinical Center",
            "CSR": "Center for Scientific Review",
            "CIT": "Center for Information Technology",
            "FIC": "John E. Fogarty International Center",
            "NCATS": "National Center for Advancing Translational Sciences",
            "NCCIH": "National Center for Complementary and Integrative Health",
            "NCI": "National Cancer Institute",
            "NCRR": "National Center for Research Resources",
            "NEI": "National Eye Institute",
            "NHGRI": "National Human Genome Research Institute",
            "NHLBI": "National Heart, Lung, and Blood Institute",
            "NIA": "National Institute on Aging",
            "NIAAA": "National Institute on Alcohol Abuse and Alcoholism",
            "NIAID": "National Institute of Allergy and Infectious Diseases",
            "NIAMS": "National Institute of Arthritis and Musculoskeletal and Skin Diseases",
            "NIBIB": "National Institute of Biomedical Imaging and Bioengineering",
            "NICHD": "Eunice Kennedy Shriver National Institute of Child Health and Human Development",
            "NIDA": "National Institute on Drug Abuse",
            "NIDCD": "National Institute on Deafness and Other Communication Disorders",
            "NIDCR": "National Institute of Dental and Craniofacial Research",
            "NIDDK": "National Institute of Diabetes and Digestive and Kidney Diseases",
            "NIEHS": "National Institute of Environmental Health Sciences",
            "NIGMS": "National Institute of General Medical Sciences",
            "NIH": "National Institutes of Health",
            "NIMH": "National Institute of Mental Health",
            "NIMHD": "National Institute on Minority Health and Health Disparities",
            "NINDS": "National Institute of Neurological Disorders and Stroke",
            "NINR": "National Institute of Nursing Research",
            "NLM": "National Library of Medicine",
            "OD": "Office of the Director"
        }
        return full_names.get(code, code)
    
    @property
    def full_name(self) -> str:
        """Get the full name of this agency"""
        return self.get_full_name(self.value)

class SearchOperator(str, Enum):
    """How to combine multiple search terms."""
    ALL = "all"
    OR = "or"
    AND = "and"
    ADVANCED = "advanced"

    @property
    def description(self) -> str:
        return {
            "all": "for searching text in all search fields (title, abstract, scientific terms)",
            "or": "projects that contain at least one of the terms entered will be retrieved. Use quotes(\") around the entered text to search for exact phrases",
            "and": "projects in which all of the search terms are found within the title, abstract, or scientific terms will be retrieved",
            "advanced": "provides additional capability to narrow selection criteria more precisely and evaluate complex entries such as chemical references",
        }[self.value]

class SearchField(str, Enum):
    """Fields to search in."""
    PROJECT_TITLE = "projecttitle"
    TERMS = "terms"
    ABSTRACT = "abstract"

    @property
    def description(self) -> str:
        return {
            "projecttitle": "Search within project titles.",
            "terms": "Search indexed NIH RePORTER terms.",
            "abstract": "Search within project abstracts.",
        }[self.value]

class AdvancedTextSearch(BaseModel):
    operator: SearchOperator = Field(
        default=SearchOperator.ALL,
        description="How to combine multiple search terms"
    )
    search_field: Union[SearchField, List[SearchField]] = Field(
        default=[SearchField.PROJECT_TITLE,SearchField.ABSTRACT,SearchField.TERMS],
        description="Single field or list of fields to search"
    )
    search_text: str = Field(
        ..., 
        description="Text to search for"
    )

    @field_validator("search_field", mode="before")
    def coerce_fields(cls, v):
        """Allow lists of strings or enums; convert everything to list of SearchField if possible."""
        if isinstance(v, str):
            v = [v]  # single string -> list
        if isinstance(v, list):
            out = []
            for f in v:
                if isinstance(f, SearchField):
                    out.append(f)
                elif isinstance(f, str):
                    f_lower = f.lower()
                    # match string to enum value
                    for field in SearchField:
                        if f_lower == field.value:
                            out.append(field)
                            break
                    else:
                        # leave as plain string if not matched
                        out.append(f)
                else:
                    out.append(f)
            return out
        return v

class ProjectNum(BaseModel):
    project_num: str = Field(
        ..., 
        description="Unique project identifier assigned by NIH RePORTER",
        min_length=1,
        examples=["1F32AG052995-01A1", "7R01DA034777-04", "1F32DK109635-01A1"]
    )

    @field_validator('project_num')
    @classmethod
    def validate_project_num(cls, v: str) -> str:
        # Remove any whitespace
        v = v.strip()
        
        # This is a loose check since formats can vary
        if not v:
            raise ValueError("Project number cannot be empty")
        
        return v.upper()  # Normalize to uppercase

class SearchParams(BaseModel):
    # required 
    advanced_text_search: Optional[AdvancedTextSearch] = Field(None, description="text search string and search parameters")

    # optional filters 
    years: Optional[List[int]] = Field(None, description="List of fiscal years where projects are active (e.g. [2023, 2024])")
    agencies: Optional[List[NIHAgency]] = Field([NIHAgency.NIH], description="the agency providing funding for the grant")
    organizations: Optional[List[str]] = Field(None, description="List of organization names who received funding (e.g. ['Johns Hopkins University'])")
    pi_name: Optional[str] = Field(None, description="Name of the grant's principal investigator (e.g. 'Allyson Sgro')")
    project_nums: Optional[List[ProjectNum]] = Field(None, description="Unique project identifier(s) assigned by NIH RePORTER (e.g. '1F32AG052995-01A1')")

    def to_api_criteria(self):
        """Convert to API criteria format"""
        criteria = {}
        
        # Add advanced text search if provided
        if self.advanced_text_search:
            ats = self.advanced_text_search
            sf = ats.search_field

            # Normalize to the comma-separated string the API expects
            if isinstance(sf, list):
                search_field_str = ", ".join(
                    s.value if isinstance(s, SearchField) else str(s) for s in sf
                )
            elif isinstance(sf, SearchField):
                search_field_str = sf.value
            else:
                # Already a string (or something else) — use as-is
                search_field_str = str(sf)

            criteria["advanced_text_search"] = {
                "search_text": ats.search_text,
                "search_field": search_field_str,
                "operator": ats.operator.value
            }

        # Add other filters
        if self.years:
            criteria["fiscal_years"] = self.years
        if self.agencies:
            criteria["agencies"] = [a.value if hasattr(a, 'value') else a for a in self.agencies]
        if self.organizations:
            criteria["organizations"] = self.organizations
        if self.pi_name:
            criteria["pi_names"] = [{"any_name": self.pi_name}]
        if self.project_nums:
            criteria["project_nums"] = [a.project_num for a in self.project_nums]
        
        return criteria
    

