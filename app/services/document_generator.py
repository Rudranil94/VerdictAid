from typing import Dict, Optional
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import json
from docx import Document
from app.core.config import settings

class DocumentGenerator:
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        
        # Load document templates metadata
        self.templates_meta = self._load_templates_metadata()
    
    def _load_templates_metadata(self) -> Dict:
        """Load metadata for all available templates."""
        meta_file = self.template_dir / "templates_meta.json"
        with open(meta_file, "r") as f:
            return json.load(f)
    
    async def generate_document(
        self,
        template_name: str,
        data: Dict,
        language: str,
        output_format: str = "docx"
    ) -> bytes:
        """
        Generate a legal document using template and provided data.
        
        Args:
            template_name: Name of the template to use
            data: Dictionary containing template variables
            language: Target language for the document
            output_format: Output format (docx, pdf, txt)
            
        Returns:
            bytes: Generated document in specified format
        """
        if language not in settings.SUPPORTED_LANGUAGES:
            raise ValueError(f"Language {language} not supported")
            
        # Get template metadata
        template_meta = self.templates_meta.get(template_name)
        if not template_meta:
            raise ValueError(f"Template {template_name} not found")
            
        # Load template for specified language
        template_file = f"{template_name}_{language}.jinja2"
        template = self.env.get_template(template_file)
        
        # Render template with provided data
        rendered_content = template.render(**data)
        
        # Convert to specified format
        if output_format == "docx":
            return self._convert_to_docx(rendered_content)
        elif output_format == "pdf":
            return self._convert_to_pdf(rendered_content)
        else:
            return rendered_content.encode()
    
    def _convert_to_docx(self, content: str) -> bytes:
        """Convert rendered content to DOCX format."""
        doc = Document()
        doc.add_paragraph(content)
        
        # Save to bytes
        from io import BytesIO
        buffer = BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
    
    def _convert_to_pdf(self, content: str) -> bytes:
        """Convert rendered content to PDF format."""
        # Implementation for PDF conversion
        # This would typically use a library like reportlab or WeasyPrint
        raise NotImplementedError("PDF conversion not yet implemented")
    
    async def list_available_templates(self, language: Optional[str] = None) -> Dict:
        """
        List available document templates, optionally filtered by language.
        """
        templates = self.templates_meta.copy()
        
        if language:
            templates = {
                name: meta for name, meta in templates.items()
                if language in meta.get("supported_languages", [])
            }
            
        return templates
