from bs4 import BeautifulSoup
from helper_func import col_names
import requests


class ScrapeLibgen:
    # default search type is title
    def __init__(self, query, search_type="title"):
        self.query = query
        self.search_type = search_type

        if len(self.query) < 3:
            # libgen support text length of 2
            raise Exception("Book name is too short to proceed")

    def destroy_italic_text(self, soup):
        # removes italic text from the parsed data
        title_italics = soup.find_all("i")
        for italic in title_italics:
            # Tag.decompose() removes a tag from the tree, completely destroys it and its contents
            italic.decompose()

    def search_initial_page(self):
        # https://libgen.is/search.php?req=java&column=title
        # https://libgen.is/search.php?req=operating%20system&column=title
        # %20 is defined as space  in URL-encode if query_parsed have space then it will replace by this %20
        # ASCII Value of space is %20

        url_encoder = "%20".join(self.query.split(" "))
        if self.search_type.lower() == "title":
            url = f"https://libgen.is/search.php?req={url_encoder}&column=title"
        elif self.search_type.lower() == "author":
            url = f"https://libgen.is/search.php?req={url_encoder}&column=author"
        return requests.get(url)

    def combined_data(self):
        raw_data = self.search_initial_page()
        # lxml parser is faster than built in html.parser
        print("Data parsing is in progress. Please allow some time for completion.")
        parsed_data = BeautifulSoup(raw_data.text, "lxml")

        self.destroy_italic_text(parsed_data)
        # site contains use of  4 tables tag is in table data in table 3 so as slicing at 2 as it's 0 index based
        parsed_table = parsed_data.find_all("table")[2]
        processed_data = []
        # don't scrape the table header title data scrape from index 1 to all
        # scrape all the table row data
        for row in parsed_table.find_all("tr")[1:]:
            processed_row = []
            # find all the table data inside the table row
            for td in row.find_all("td"):
                # download link contains the title attributes like <a href="somelink.com" title="Libgen.li">[2]</a>
                # other link does not contain title attribute <a href="some.link" title="">Some Person</a>

                # search for the "a" tag if the link conatain title attribute and is not empty then append to processed_row otherwise scrape the data of td using else block so that all data is preserved
                # short circuit if false
                if (
                    td.find("a")
                    and td.find("a").has_attr("title")
                    and td.find("a")["title"] != ""
                ):
                    processed_row.append(td.a["href"])
                else:
                    #  stripped_strings is used to get the text within tag. It returns an iterator of strings where leading and trailing whitespaces have been stripped.
                    # data is preserved for further use as data contains various crucial information such as title,auther name, unique id etc
                    processed_row.append("".join(td.stripped_strings))
            # append data after scraping each row
            processed_data.append(processed_row)

        # Using list comprehension to convert each row into a dictionary
        parsed_dict = [dict(zip(col_names, row)) for row in processed_data]
        print("Consolidating parsed data into linked columns.")
        return parsed_dict


class ScraperWizard:
    def search_title(self, query):
        parsed_dict = ScrapeLibgen(query, search_type="title")
        return parsed_dict.combined_data()

    def search_author(self, query):
        parsed_dict = ScrapeLibgen(query, search_type="author")
        return parsed_dict.combined_data()

    def process_download_links(self, item):
        # Make a request to the stable URL mirror_1 from item
        page = requests.get(item["Mirror_1"])
        # Parse the HTML content libgen gateway are "GET", "Cloudflare", "IPFS.io", "Infura"
        soup = BeautifulSoup(page.text, "html.parser")
        # Find all <a> tags containing certain strings : libgen gateway are "GET", "Cloudflare", "IPFS.io", "Infura"
        links = soup.find_all("a", string=["GET", "Cloudflare", "IPFS.io", "Infura"])
        # Extract the link text and href attributes into a dictionary
        # eg:  {'GET': 'https://one.pdf', 'Cloudflare': 'https://cloudflare-ipfs.com'}
        download_links = {link.string: link["href"] for link in links}
        return download_links
