from __future__ import annotations

import json
import re
from dataclasses import dataclass
from bs4 import BeautifulSoup

@dataclass
class CleanedDescription:
    "Cleaned and strucutred information extracted from Fuzu job description"
    
    description: str
    responsibilities: str | None = None
    skills: str | None = None
    qualifications: str | None = None
    experience: str | None = None
    tags: str | None = None


def clean_job_description(data: json) -> CleanedDescription:
    """
    Clean a job description and extract useful sections.

    Parameters
    ----------
    data:
        Raw Json job description.

    Returns
    -------
    CleanJobDescription
        Cleaned description and extracted job information.
    """
    description = data.get("description", None)
    
    if description is not None:
        soup = BeautifulSoup(description, "html.parser")
        
    #* -----------------------------------
    #* 1. convert html into readable text
    #* -----------------------------------
    
    #* replace <p></p> html tags with a newline
    for p in soup.find_all("<p>"):
        p.replace_with("\n")
            
    #* remove html entities
    text = soup.get_text("\n")
    text = text.replace("\xa0", " ")
    
    #* Normalize whitespace.
    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            lines.append(line)

    text = "\n".join(lines)

    #* 2. extract sections
    lines = text.splitlines()
    
    section_headers = {
        "description",
        "1. key responsibilities.",
        "reporting and accountability",
        "skills and competencies",
        "qualifications and experience.",
        "experience:",
        "role scope and career development",
        "tags",
        "reporting and accountability",
        "role scope and career development",
        "kenya",
    }
    
    sections: dict[str, list[str]] = {}
    current_section: str | None = None
    
    for line in lines:
    
        normalized = line.lower().strip()
        if normalized in section_headers:
            current_section = normalized
            sections[current_section] = []
            continue
            
        if current_section is not None:
            sections[current_section].append(line)
                
    sections = {
        section: " ".join(content).strip()
        for section, content in sections.items()
        if content
    }
    
    if sections.keys():
        try:
            return CleanedDescription(
                description= sections.get("description"),
                responsibilities= sections["1. key responsibilities."],
                skills= sections["skills and competencies"],
                qualifications= sections["qualifications and experience."],
                experience= sections["experience:"],
                tags = sections["tags"]
            )
        except Exception as e:
            return 