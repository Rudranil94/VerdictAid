from typing import Dict, List, Optional
from langchain.llms import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings

class DocumentAnalyzer:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.llm = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.llm = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
    
    async def simplify_document(self, content: str, target_language: str = "en") -> str:
        """
        Simplifies legal document content into plain language.
        """
        if not self.llm:
            return f"Document simplification is not available. Please provide an OpenAI API key."
        
        prompt = f"""
        Translate the following legal document into simple, plain language.
        Make it easy to understand while preserving all important legal meanings.
        Target language: {target_language}
        
        Document:
        {content}
        """
        return await self._process_with_llm(prompt)
    
    async def analyze_risks(self, content: str) -> Dict[str, List[str]]:
        """
        Analyzes legal risks in the document.
        """
        if not self.llm:
            return {
                "risks": ["Risk analysis is not available. Please provide an OpenAI API key."],
                "recommendations": ["Please configure OpenAI API key to enable risk analysis."]
            }
        
        prompt = f"""
        Analyze the following legal document and identify potential risks
        and compliance issues. Format the response as a JSON with
        'risks' and 'recommendations' keys.
        
        Document:
        {content}
        """
        return await self._process_with_llm(prompt)
    
    async def extract_key_terms(self, content: str) -> List[Dict[str, str]]:
        """
        Extracts and explains key legal terms from the document.
        """
        if not self.llm:
            return [{"term": "Key term extraction", "explanation": "Not available. Please provide an OpenAI API key."}]
        
        prompt = f"""
        Extract and explain key legal terms from the following document.
        Format the response as a list of JSON objects with 'term' and
        'explanation' keys.
        
        Document:
        {content}
        """
        return await self._process_with_llm(prompt)
    
    async def _process_with_llm(self, prompt: str) -> any:
        """
        Process prompt using the LLM.
        """
        if not self.llm:
            raise ValueError("LLM is not initialized. Please provide an OpenAI API key.")
        
        try:
            response = await self.llm.apredict(prompt)
            return response
        except Exception as e:
            raise ValueError(f"Error processing with LLM: {str(e)}")
