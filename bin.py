import aiohttp
import asyncio
import logging
from typing import Dict, Optional, TypedDict
from aiohttp import ClientError, ClientResponseError, ClientConnectorError

# Configure logger
logger = logging.getLogger(__name__)

# Updated URL
BINLIST_URL = "https://bins.antipublic.cc/bins/{}"

# Type hint for return value
class BINInfo(TypedDict, total=False):
    bin: Optional[str]
    length: str
    luhn: str
    scheme: Optional[str]
    type: Optional[str]
    brand: Optional[str]
    bank: Optional[str]
    bank_phone: str
    bank_url: str
    country: Optional[str]
    country_emoji: Optional[str]
    error: Optional[str]

async def get_bin_info(bin_number: str, max_retries: int = 3) -> BINInfo:
    """
    Fetch BIN (Bank Identification Number) information from the antipublic.cc API.
    
    Args:
        bin_number (str): The BIN number (first 6-8 digits of a card)
        max_retries (int): Maximum number of retry attempts (default: 3)
    
    Returns:
        dict: Dictionary containing BIN information with the following keys:
            - bin: The BIN number
            - length: Always "N/A" (not provided by API)
            - luhn: Always "N/A" (not provided by API)
            - scheme: Card scheme (VISA, MASTERCARD, etc.)
            - type: Card type (credit, debit, etc.)
            - brand: Card level/brand (CLASSIC, PLATINUM, etc.)
            - bank: Issuing bank name
            - bank_phone: Always "N/A" (not provided by API)
            - bank_url: Always "N/A" (not provided by API)
            - country: Country name
            - country_emoji: Country flag emoji
            - error: Error message if something went wrong
    
    Example:
        >>> info = await get_bin_info("414720")
        >>> print(info["scheme"])
        'VISA'
    
    Note:
        The API endpoint used: https://bins.antipublic.cc/bins/{bin}
    """
    # Clean and validate BIN number
    original_bin = bin_number
    bin_number = ''.join(filter(str.isdigit, bin_number))
    
    if not bin_number or len(bin_number) < 6:
        logger.warning(f"Invalid BIN provided: {original_bin}")
        return {"error": "Invalid BIN. Must be at least 6 digits."}
    
    # Truncate to first 8 digits (typical BIN length)
    bin_number = bin_number[:8]
    logger.debug(f"Fetching BIN info for: {bin_number}")
    
    # Set timeout
    timeout = aiohttp.ClientTimeout(total=10)
    
    # Retry logic
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(BINLIST_URL.format(bin_number)) as resp:
                    
                    # Handle rate limiting with retry
                    if resp.status == 429:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(f"Rate limited. Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        return {"error": "Rate limit exceeded. Try again later."}
                    
                    # Handle not found
                    if resp.status == 404:
                        logger.info(f"BIN not found: {bin_number}")
                        return {"error": "BIN not found."}
                    
                    # Handle other HTTP errors
                    if resp.status != 200:
                        logger.error(f"API request failed with status {resp.status} for BIN {bin_number}")
                        return {"error": f"API request failed (status {resp.status})"}
                    
                    # Parse response
                    data = await resp.json()
                    
                    # Validate response structure
                    if not isinstance(data, dict):
                        logger.error(f"Invalid response format for BIN {bin_number}")
                        return {"error": "Invalid response format from API"}
                    
                    # Check if we got meaningful data
                    if not data.get("bin") and not data.get("brand"):
                        logger.warning(f"Incomplete data received for BIN {bin_number}")
                        return {"error": "Incomplete data received from API"}
                    
                    # Map response to expected format
                    result = {
                        "bin": data.get("bin"),
                        "length": "N/A",
                        "luhn": "N/A",
                        "scheme": data.get("brand"),
                        "type": data.get("type"),
                        "brand": data.get("level"),
                        "bank": data.get("bank"),
                        "bank_phone": "N/A",
                        "bank_url": "N/A",
                        "country": data.get("country_name"),
                        "country_emoji": data.get("country_flag"),
                    }
                    
                    logger.info(f"Successfully fetched BIN info for: {bin_number}")
                    return result
                    
        except ClientResponseError as e:
            logger.error(f"HTTP error for BIN {bin_number}: {e.status} - {e.message}")
            if attempt == max_retries - 1:
                return {"error": f"HTTP error {e.status}: {e.message}"}
                
        except ClientConnectorError as e:
            logger.error(f"Connection error for BIN {bin_number}: {str(e)}")
            if attempt == max_retries - 1:
                return {"error": f"Connection error: {str(e)}"}
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout error for BIN {bin_number}")
            if attempt == max_retries - 1:
                return {"error": "Request timeout"}
                
        except Exception as e:
            logger.error(f"Unexpected error for BIN {bin_number}: {str(e)}")
            if attempt == max_retries - 1:
                return {"error": f"Exception: {str(e)}"}
        
        # Wait before retry (except on last attempt)
        if attempt < max_retries - 1:
            await asyncio.sleep(1)
    
    return {"error": f"Failed after {max_retries} attempts"}