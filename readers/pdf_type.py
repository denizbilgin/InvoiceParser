from enum import Enum


class PDFType(Enum):
    TEXT_BASED = 'text_based'
    SCANNED_IMAGE = 'scanned_image'
    MIXED = 'mixed'
