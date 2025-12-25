import os
import re
import time
from io import BytesIO
from urllib.parse import urljoin

import PyPDF2
import requests
from bs4 import BeautifulSoup
from googlesearch import search


def fetch_supplementary_info_from_doi(doi: str, output_dir: str = "supplementary_info"):
    """Fetches supplementary information for a paper given its DOI and returns a research log.

    Args:
        doi: The paper DOI.
        output_dir: Directory to save supplementary files.

    Returns:
        dict: A dictionary containing a research log and the downloaded file paths.

    """
    research_log = []
    research_log.append(f"Starting process for DOI: {doi}")

    # CrossRef API to resolve DOI to a publisher page
    crossref_url = f"https://doi.org/{doi}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(crossref_url, headers=headers)

    if response.status_code != 200:
        log_message = f"Failed to resolve DOI: {doi}. Status Code: {response.status_code}"
        research_log.append(log_message)
        return {"log": research_log, "files": []}

    publisher_url = response.url
    research_log.append(f"Resolved DOI to publisher page: {publisher_url}")

    # Fetch publisher page
    response = requests.get(publisher_url, headers=headers)
    if response.status_code != 200:
        log_message = f"Failed to access publisher page for DOI {doi}."
        research_log.append(log_message)
        return {"log": research_log, "files": []}

    # Parse page content
    soup = BeautifulSoup(response.content, "html.parser")
    supplementary_links = []

    # Look for supplementary materials by keywords or links
    for link in soup.find_all("a", href=True):
        href = link.get("href")
        text = link.get_text().lower()
        if "supplementary" in text or "supplemental" in text or "appendix" in text:
            full_url = urljoin(publisher_url, href)
            supplementary_links.append(full_url)
            research_log.append(f"Found supplementary material link: {full_url}")

    if not supplementary_links:
        log_message = f"No supplementary materials found for DOI {doi}."
        research_log.append(log_message)
        return research_log

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    research_log.append(f"Created output directory: {output_dir}")

    # Download supplementary materials
    downloaded_files = []
    for link in supplementary_links:
        file_name = os.path.join(output_dir, link.split("/")[-1])
        file_response = requests.get(link, headers=headers)
        if file_response.status_code == 200:
            with open(file_name, "wb") as f:
                f.write(file_response.content)
            downloaded_files.append(file_name)
            research_log.append(f"Downloaded file: {file_name}")
        else:
            research_log.append(f"Failed to download file from {link}")

    if downloaded_files:
        research_log.append(f"Successfully downloaded {len(downloaded_files)} file(s).")
    else:
        research_log.append(f"No files could be downloaded for DOI {doi}.")

    return "\n".join(research_log)


def query_arxiv(query: str, max_papers: int = 10) -> str:
    """Query arXiv for papers based on the provided search query.

    Parameters
    ----------
    - query (str): The search query string.
    - max_papers (int): The maximum number of papers to retrieve (default: 10).

    Returns
    -------
    - str: The formatted search results or an error message.

    """
    import arxiv

    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_papers, sort_by=arxiv.SortCriterion.Relevance)
        results = "\n\n".join([f"Title: {paper.title}\nSummary: {paper.summary}" for paper in client.results(search)])
        return results if results else "No papers found on arXiv."
    except Exception as e:
        return f"Error querying arXiv: {e}"


def query_scholar(query: str) -> str:
    """Query Google Scholar for papers based on the provided search query.

    Parameters
    ----------
    - query (str): The search query string.

    Returns
    -------
    - str: The first search result formatted or an error message.

    """
    from scholarly import ProxyGenerator, scholarly

    # Set up a ProxyGenerator object to use free proxies
    # This needs to be done only once per session
    pg = ProxyGenerator()
    pg.FreeProxies()
    scholarly.use_proxy(pg)
    try:
        search_query = scholarly.search_pubs(query)
        result = next(search_query, None)
        if result:
            return f"Title: {result['bib']['title']}\nYear: {result['bib']['pub_year']}\nVenue: {result['bib']['venue']}\nAbstract: {result['bib']['abstract']}"
        else:
            return "No results found on Google Scholar."
    except Exception as e:
        return f"Error querying Google Scholar: {e}"


def query_pubmed(query: str, max_papers: int = 10, max_retries: int = 3) -> list[dict]:
    """Query PubMed for papers based on the provided search query.

    ⚠️ IMPORTANT: This function returns a LIST OF DICTS, not a string.

    ⚠️ TO DISPLAY RESULTS NICELY, ALWAYS use print_pubmed_results():
        papers = query_pubmed("diabetes 2025", max_papers=10)
        print(print_pubmed_results("糖尿病研究", papers, top_n=5))

    DO NOT print the list directly:
        print(papers)  # ❌ This will show ugly Python list format

    Parameters
    ----------
    - query (str): The search query string.
    - max_papers (int): The maximum number of papers to retrieve (default: 10).
    - max_retries (int): Maximum number of retry attempts with modified queries (default: 3).

    Returns
    -------
    - list[dict]: A list of paper dictionaries with keys: 'title', 'abstract', 'journal'
                   Each dict: {'title': str, 'abstract': str, 'journal': str}

    """
    from pymed import PubMed

    try:
        pubmed = PubMed(tool="MyTool", email="your-email@example.com")  # Update with a valid email address

        # Initial attempt
        papers = list(pubmed.query(query, max_results=max_papers))

        # Retry with modified queries if no results
        retries = 0
        while not papers and retries < max_retries:
            retries += 1
            # Simplify query with each retry by removing the last word
            simplified_query = " ".join(query.split()[:-retries]) if len(query.split()) > retries else query
            time.sleep(1)  # Add delay between requests
            papers = list(pubmed.query(simplified_query, max_results=max_papers))

        if papers:
            results = []
            for paper in papers:
                # Handle different article types (PubMedArticle vs PubMedBookArticle)
                title = paper.title if hasattr(paper, "title") else "N/A"
                # abstract can be None (has attribute but value is None)
                abstract = paper.abstract if (hasattr(paper, "abstract") and paper.abstract) else "N/A"

                # PubMedBookArticle has 'publisher' instead of 'journal'
                if hasattr(paper, "journal"):
                    journal = paper.journal
                elif hasattr(paper, "publisher"):
                    journal = f"Publisher: {paper.publisher}"
                else:
                    journal = "N/A"

                # Return as dict, not formatted string
                results.append({
                    "title": title,
                    "abstract": abstract,
                    "journal": journal
                })

            return results
        else:
            return []
    except Exception as e:
        return f"Error querying PubMed: {e}"


def format_pubmed_results(papers: list[dict], max_abstract_length: int = 500) -> str:
    """Format PubMed query results as a readable string.

    Parameters
    ----------
    - papers (list[dict]): The list of paper dictionaries from query_pubmed()
    - max_abstract_length (int): Maximum length of abstract to show (default: 500)

    Returns
    -------
    - str: Formatted string with Title, Abstract, and Journal for each paper

    Usage
    -----
    papers = query_pubmed("diabetes 2025", max_papers=3)
    print(format_pubmed_results(papers))
    """
    if not papers:
        return "No papers found."

    formatted = []
    for paper in papers:
        title = paper.get("title", "N/A")
        abstract = paper.get("abstract", "N/A")
        journal = paper.get("journal", "N/A")

        # Truncate abstract if too long
        if len(abstract) > max_abstract_length:
            abstract = abstract[:max_abstract_length] + "..."

        formatted.append(f"Title: {title}\nAbstract: {abstract}\nJournal: {journal}")

    return "\n\n".join(formatted)


def print_pubmed_results(category_name: str, papers: list[dict], top_n: int = 5, max_abstract_length: int = 300) -> str:
    """Print PubMed search results in a formatted, user-friendly way.

    This function is designed for LLM agents to display search results consistently.

    Parameters
    ----------
    - category_name (str): Name of the search category (e.g., "心衰治疗新进展")
    - papers (list[dict]): The list of paper dictionaries from query_pubmed()
    - top_n (int): Number of top papers to display (default: 5)
    - max_abstract_length (int): Maximum length of abstract to show (default: 300)

    Returns
    -------
    - str: Formatted string ready for printing

    Usage
    -----
    papers = query_pubmed("heart failure 2025", max_papers=20)
    output = print_pubmed_results("心衰治疗新进展", papers, top_n=5)
    print(output)
    """
    if not papers:
        return f"\n{'='*60}\n【{category_name}】\n{'='*60}\n\n未找到相关文献\n"

    lines = []
    lines.append("=" * 60)
    lines.append(f"【{category_name}】")
    lines.append("=" * 60)
    lines.append(f"\n前 {min(top_n, len(papers))} 篇文章如下：\n")

    for i, paper in enumerate(papers[:top_n], 1):
        title = paper.get("title", "N/A")
        journal = paper.get("journal", "N/A")
        abstract = paper.get("abstract")

        # Handle None or empty abstract
        if not abstract:
            abstract = "N/A"
        elif len(abstract) > max_abstract_length:
            abstract = abstract[:max_abstract_length] + "..."

        lines.append(f"{i}. 论文 {i}")
        lines.append(f"   标题: {title}")
        lines.append(f"   期刊: {journal}")
        lines.append(f"   摘要: {abstract}")
        lines.append("")

    return "\n".join(lines)


def search_google(query: str, num_results: int = 3, language: str = "en") -> str:
    """Search using Google search.

    ⚠️ NOTE: Google often blocks automated search requests. This function may not work
    reliably in all environments. Consider using advanced_web_search_claude() as an
    alternative.

    Args:
        query (str): The search query (e.g., "protocol text or seach question")
        num_results (int): Number of results to return (default: 3)
        language (str): Language code for search results (default: 'en')

    Returns:
        str: Formatted search results with URLs, or error message if search fails

    """
    try:
        results_string = ""
        search_query = f"{query}"

        print(f"Searching for {search_query} with {num_results} results and {language} language")

        # googlesearch.search() uses 'stop' to limit number of results
        # Returns URLs only (advanced=True is not supported in current version)
        urls = search(search_query, tld='com', lang=language, num=10, stop=num_results, pause=2.0)

        result_count = 0
        for i, url in enumerate(urls, 1):
            result_count += 1
            print(f"Found result {i}: {url[:80]}...")
            results_string += f"Result {i}:\nURL: {url}\n\n"

        if result_count == 0:
            return "No results found. Google may be blocking automated searches. Try using advanced_web_search_claude() instead."

    except Exception as e:
        error_msg = f"Error performing search: {str(e)}"
        print(error_msg)
        return error_msg

    return results_string


def advanced_web_search_claude(
    query: str,
    max_searches: int = 1,
    max_retries: int = 3,
) -> tuple[str, list[dict[str, str]], list]:
    """
    Initiate an advanced web search by launching a specialized agent to collect relevant information and citations through multiple rounds of web searches for a given query.
    Craft the query carefully for the search agent to find the most relevant information.

    Parameters
    ----------
    query : str
        The search phrase you want Claude to look up.
    max_searches : int, optional
        Upper-bound on searches Claude may issue inside this request.
    max_retries : int, optional
        Maximum number of retry attempts with exponential backoff.

    Returns
    -------
    full_text : str
        A formatted string containing the full text response from Claude and the citations.
    """
    import random

    import anthropic

    try:
        from biomni.config import default_config

        model = default_config.llm
        api_key = default_config.api_key
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")
    except ImportError:
        model = "claude-4-sonnet-latest"
        api_key = os.getenv("ANTHROPIC_API_KEY")

    if "claude" not in model:
        raise ValueError("Model must be a Claude model.")

    if not api_key:
        raise ValueError("Set your api_key explicitly.")

    client = anthropic.Anthropic(api_key=api_key)
    tool_def = {
        "type": "web_search_20250305",
        "name": "web_search",
        "max_uses": max_searches,
    }

    delay = random.randint(1, 10)

    for attempt in range(1, max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": query}],
                tools=[tool_def],
            )

            paragraphs, citations = [], []
            response.content = response.content
            formatted_response = ""
            for blk in response.content:
                if blk.type == "text":
                    paragraphs.append(blk.text)
                    formatted_response += blk.text

                    if blk.citations:
                        for cite in blk.citations:
                            citations.append({"url": cite.url, "title": cite.title, "cited_text": cite.cited_text})
                            formatted_response += f"(Citation: {cite.title} - {cite.url})"
            return formatted_response

        except Exception as e:
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 2
                continue
            print(f"Error performing web search after {max_retries} attempts: {str(e)}")
            return f"Error performing web search after {max_retries} attempts: {str(e)}"


def extract_url_content(url: str) -> str:
    """Extract the text content of a webpage using requests and BeautifulSoup.

    Args:
        url: Webpage URL to extract content from

    Returns:
        Text content of the webpage

    """
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    # Check if the response is in text format
    if "text/plain" in response.headers.get("Content-Type", "") or "application/json" in response.headers.get(
        "Content-Type", ""
    ):
        return response.text.strip()  # Return plain text or JSON response directly

    # If it's HTML, use BeautifulSoup to parse
    soup = BeautifulSoup(response.text, "html.parser")

    # Try to find main content first, fallback to body
    content = soup.find("main") or soup.find("article") or soup.body

    # Remove unwanted elements
    for element in content(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
        element.decompose()

    # Extract text with better formatting
    paragraphs = content.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"])
    cleaned_text = []

    for p in paragraphs:
        text = p.get_text().strip()
        if text:  # Only add non-empty paragraphs
            cleaned_text.append(text)

    return "\n\n".join(cleaned_text)


def extract_pdf_content(url: str) -> str:
    """Extract the text content of a PDF file given its URL.

    Args:
        url: URL of the PDF file to extract text from

    Returns:
        The extracted text content from the PDF

    """
    try:
        # Check if the URL ends with .pdf
        if not url.lower().endswith(".pdf"):
            # If not, try to find a PDF link on the page
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Look for PDF links in the HTML content
                pdf_links = re.findall(r'href=[\'"]([^\'"]+\.pdf)[\'"]', response.text)
                if pdf_links:
                    # Use the first PDF link found
                    if not pdf_links[0].startswith("http"):
                        # Handle relative URLs
                        base_url = "/".join(url.split("/")[:3])
                        url = base_url + pdf_links[0] if pdf_links[0].startswith("/") else base_url + "/" + pdf_links[0]
                    else:
                        url = pdf_links[0]
                else:
                    return f"No PDF file found at {url}. Please provide a direct link to a PDF file."

        # Download the PDF
        response = requests.get(url, timeout=30)

        # Check if we actually got a PDF file (by checking content type or magic bytes)
        content_type = response.headers.get("Content-Type", "").lower()
        if "application/pdf" not in content_type and not response.content.startswith(b"%PDF"):
            return f"The URL did not return a valid PDF file. Content type: {content_type}"

        pdf_file = BytesIO(response.content)

        # Try with PyPDF2 first
        try:
            text = ""
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")

        # Clean up the text
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            return "The PDF file did not contain any extractable text. It may be an image-based PDF requiring OCR."

        return text

    except requests.exceptions.RequestException as e:
        return f"Error downloading PDF: {str(e)}"
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"
