from typing import Any, Dict, Optional
from .base_agent import BaseAgent
from pathlib import Path
import asyncio
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import config
from mistralai.async_client import MistralAsyncClient
from mistralai.models.chat_completion import ChatMessage
import base64
import io
from database.db import db

class OCRAgent(BaseAgent):
    def __init__(self):
        super().__init__("OCR Agent", layer=1)
        self.mistral_client = None
        if config.MISTRAL_API_KEY:
            self.mistral_client = MistralAsyncClient(api_key=config.MISTRAL_API_KEY)

    async def execute(self, input_data: Any, parameters: Dict = None) -> Dict[str, Any]:
        """
        Perform OCR on documents using Mistral AI and pytesseract

        Args:
            input_data: Can be file path, image data, or text content
            parameters: Configuration including max_pages, language, dpi, etc.

        Returns:
            Dictionary containing extracted text and metadata
        """
        params = parameters or {}
        max_pages = params.get('maxPages', config.OCR_MAX_PAGES)
        language = params.get('language', 'en')
        dpi = params.get('dpi', 300)
        use_mistral = params.get('ocrEngine') == 'mistral' and self.mistral_client
        extract_images = params.get('extractImages', True)
        preserve_layout = params.get('preserveLayout', True)

        try:
            # Handle different input types
            if isinstance(input_data, str):
                # Check if it's a numeric document_id
                if input_data.isdigit() and db.pool:
                    # Try to resolve document_id to file_path
                    file_path = await self._get_file_path_from_document_id(int(input_data))
                    if file_path:
                        return await self._process_file(
                            file_path, max_pages, language, dpi, use_mistral, preserve_layout
                        )
                
                # Check if it's a file path
                file_path = Path(input_data)
                if file_path.exists():
                    return await self._process_file(
                        file_path, max_pages, language, dpi, use_mistral, preserve_layout
                    )
                else:
                    # It's plain text, return as-is
                    return {
                        "extracted_text": input_data,
                        "total_words": len(input_data.split()),
                        "page_count": 1,
                        "method": "direct_text",
                        "confidence": 1.0
                    }
            elif isinstance(input_data, dict):
                # Handle processed document data
                if 'file_path' in input_data:
                    return await self._process_file(
                        Path(input_data['file_path']),
                        max_pages, language, dpi, use_mistral, preserve_layout
                    )
                elif 'document_id' in input_data and db.pool:
                    # Resolve document_id to file_path
                    file_path = await self._get_file_path_from_document_id(input_data['document_id'])
                    if file_path:
                        return await self._process_file(
                            file_path, max_pages, language, dpi, use_mistral, preserve_layout
                        )
                elif 'full_text' in input_data:
                    return {
                        "extracted_text": input_data['full_text'],
                        "total_words": len(input_data['full_text'].split()),
                        "page_count": input_data.get('num_pages', 1),
                        "method": "pre_extracted",
                        "confidence": 1.0
                    }

            return {
                "extracted_text": str(input_data),
                "total_words": len(str(input_data).split()),
                "page_count": 1,
                "method": "fallback",
                "confidence": 0.5
            }

        except Exception as e:
            raise Exception(f"OCR processing failed: {str(e)}")

    async def _get_file_path_from_document_id(self, document_id: int) -> Optional[Path]:
        """Get file path from document_id"""
        if not db.pool:
            return None
        
        try:
            # Get document info from database
            doc = await db.fetchrow("""
                SELECT filename FROM documents WHERE id = $1
            """, document_id)
            
            if not doc:
                return None
            
            # Find file path using pattern matching
            file_pattern = f"*_{doc['filename']}"
            matching_files = list(config.UPLOAD_FOLDER.glob(file_pattern))
            
            if matching_files:
                return Path(matching_files[0])
            
            return None
        except Exception as e:
            print(f"Error getting file path from document_id {document_id}: {e}")
            return None

    async def _process_file(
        self,
        file_path: Path,
        max_pages: int,
        language: str,
        dpi: int,
        use_mistral: bool,
        preserve_layout: bool
    ) -> Dict[str, Any]:
        """Process a file (PDF or image) for OCR"""

        file_ext = file_path.suffix.lower()

        if file_ext == '.pdf':
            return await self._process_pdf(
                file_path, max_pages, language, dpi, use_mistral, preserve_layout
            )
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return await self._process_image(
                file_path, language, use_mistral, preserve_layout
            )
        else:
            raise Exception(f"Unsupported file type: {file_ext}")

    async def _process_pdf(
        self,
        pdf_path: Path,
        max_pages: int,
        language: str,
        dpi: int,
        use_mistral: bool,
        preserve_layout: bool
    ) -> Dict[str, Any]:
        """Process PDF file and extract text from images"""

        try:
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=1,
                last_page=min(max_pages, 1000)  # Safety limit
            )

            pages_data = []
            total_confidence = 0

            for page_num, image in enumerate(images[:max_pages], start=1):
                if use_mistral:
                    # Use Mistral Vision API for OCR
                    page_result = await self._ocr_with_mistral(image, preserve_layout)
                else:
                    # Use pytesseract
                    page_result = await self._ocr_with_tesseract(
                        image, language, preserve_layout
                    )

                pages_data.append({
                    "page_number": page_num,
                    "text": page_result['text'],
                    "confidence": page_result['confidence'],
                    "word_count": len(page_result['text'].split())
                })

                total_confidence += page_result['confidence']

            # Combine all pages
            full_text = "\n\n".join([p['text'] for p in pages_data])
            avg_confidence = total_confidence / len(pages_data) if pages_data else 0

            return {
                "extracted_text": full_text,
                "pages": pages_data,
                "page_count": len(pages_data),
                "total_words": len(full_text.split()),
                "average_confidence": round(avg_confidence, 3),
                "method": "mistral_vision" if use_mistral else "pytesseract",
                "dpi": dpi,
                "language": language
            }

        except Exception as e:
            raise Exception(f"PDF processing failed: {str(e)}")

    async def _process_image(
        self,
        image_path: Path,
        language: str,
        use_mistral: bool,
        preserve_layout: bool
    ) -> Dict[str, Any]:
        """Process single image file for OCR"""

        try:
            image = Image.open(image_path)

            if use_mistral:
                result = await self._ocr_with_mistral(image, preserve_layout)
            else:
                result = await self._ocr_with_tesseract(image, language, preserve_layout)

            return {
                "extracted_text": result['text'],
                "total_words": len(result['text'].split()),
                "confidence": result['confidence'],
                "page_count": 1,
                "method": "mistral_vision" if use_mistral else "pytesseract",
                "image_size": image.size,
                "language": language
            }

        except Exception as e:
            raise Exception(f"Image processing failed: {str(e)}")

    async def _ocr_with_tesseract(
        self,
        image: Image.Image,
        language: str,
        preserve_layout: bool
    ) -> Dict[str, Any]:
        """Perform OCR using pytesseract"""

        try:
            # Configure tesseract
            config_str = '--psm 1' if preserve_layout else '--psm 3'

            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=language,
                config=config_str
            )

            # Get confidence data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "text": text.strip(),
                "confidence": avg_confidence / 100  # Normalize to 0-1
            }

        except Exception as e:
            # Fallback to basic extraction
            return {
                "text": pytesseract.image_to_string(image),
                "confidence": 0.0
            }

    async def _ocr_with_mistral(
        self,
        image: Image.Image,
        preserve_layout: bool
    ) -> Dict[str, Any]:
        """Perform OCR using Mistral Vision API"""

        if not self.mistral_client:
            raise Exception("Mistral API key not configured")

        try:
            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_b64 = base64.b64encode(buffer.getvalue()).decode()

            # Create prompt based on layout preference
            if preserve_layout:
                prompt = """Extract all text from this image while preserving the original layout and structure.
                Maintain paragraphs, line breaks, and formatting as much as possible.
                Return only the extracted text without any additional comments."""
            else:
                prompt = """Extract all text from this image.
                Return the text in a clean, readable format without preserving the original layout.
                Return only the extracted text without any additional comments."""

            # Call Mistral Vision API
            response = await self.mistral_client.chat(
                model="pixtral-12b-2409",  # Mistral's vision model
                messages=[
                    ChatMessage(
                        role="user",
                        content=[
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": f"data:image/png;base64,{image_b64}"
                            }
                        ]
                    )
                ]
            )

            extracted_text = response.choices[0].message.content

            return {
                "text": extracted_text.strip(),
                "confidence": 0.95  # Mistral typically has high confidence
            }

        except Exception as e:
            raise Exception(f"Mistral OCR failed: {str(e)}")
