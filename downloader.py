import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from bs4 import BeautifulSoup
import time
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import requests
from tqdm import tqdm

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",  # Do Not Track Requests Header
    "Connection": "keep-alive"
}


# 设置 Edge 的一些选项以启用自动下载
edge_options = Options()
download_dir = "papers"  # 例如: "C:/Downloads"

# 配置下载选项
prefs = {
    "download.default_directory": download_dir,  # 指定下载目录
    "download.prompt_for_download": False,  # 禁用下载前的弹窗
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True  # 自动打开 PDF 文件而不是在浏览器中预览
}

edge_options.add_experimental_option("prefs", prefs)

# 手动指定 Edge WebDriver 的路径
webdriver_path = 'edgedriver_win64/msedgedriver.exe'  # 确保这个路径是正确的

# 初始化 Edge WebDriver
service = Service(webdriver_path)
driver = webdriver.Edge(service=service)

# 如果不存在，创建文件夹用于存储下载的论文
if not os.path.exists("papers"):
    os.makedirs("papers")

for i in tqdm(range(1, 30)):

    # 会议主页 URL
    conference_url = f"https://ieeexplore.ieee.org/xpl/conhome/10445798/proceeding?isnumber=10445803&sortType=vol-only-seq&pageNumber={i}&rowsPerPage=100"

    print(f"Scrawling {conference_url}")

    # 使用 WebDriver 打开页面
    driver.get(conference_url)

    # 等待一段时间，确保页面完全加载
    time.sleep(30)

    # 获取页面源代码
    html = driver.page_source

    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html, "html.parser")

    # 查找所有论文链接
    paper_links = soup.find_all("a", href=lambda href: href and "/document/" in href)

    unique_links = set()
    new_paper_links = []

    for link in paper_links:
        href = link.get("href")
        if href not in unique_links:
            unique_links.add(href)
            new_paper_links.append(link)

    paper_links = new_paper_links

    # 遍历每个论文链接
    for link in tqdm(paper_links):
        try:
            paper_url = "https://ieeexplore.ieee.org" + link.get("href")

            # 使用 WebDriver 打开论文页面
            driver.get(paper_url)

            # 为页面加载等待
            time.sleep(10)

            # 获取论文页面的 HTML 内容
            paper_html = driver.page_source
            paper_soup = BeautifulSoup(paper_html, "html.parser")

            # 查找论文标题
            title_tag = paper_soup.find("h1", class_="document-title")
            title = title_tag.text.strip() if title_tag else "Untitled"

            # 查找PDF下载链接 (注意：IEEE Xplore 可能不允许直接下载 PDF)
            pdf_link = paper_soup.find("a", class_="pdf-btn-link")
            pdf_url = "https://ieeexplore.ieee.org" + pdf_link["href"] if pdf_link else None

            if pdf_url:

                # 下载 PDF 文件 (这可能不会工作，因为 IEEE Xplore 可能需要登录或其他权限)
                pdf_response = driver.get(pdf_url)
                # 等待下载
                time.sleep(10)

                # 获取论文页面的 HTML 内容
                paper_html = driver.page_source
                paper_soup = BeautifulSoup(paper_html, "html.parser")

                # 查找页面中的<iframe>元素
                iframe = paper_soup.find("iframe", src=lambda x: x and "ieeexplore.ieee.org" in x)

                if iframe and 'src' in iframe.attrs:
                    pdf_url = iframe['src']

                    # 使用requests库下载PDF文件
                    pdf_response = requests.get(pdf_url, headers=headers)

                    # 确保请求成功
                    if pdf_response.status_code == 200:
                        # 生成文件名
                        filename = title.replace(" ", "_") + ".pdf"
                        # 去掉文件名中的非法字符
                        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
                        filename = os.path.join(download_dir, filename)

                        # 写入文件内容
                        with open(filename, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"Downloaded: {filename}")
                    else:
                        print(f"Failed to download PDF for: {title}, Status code: {pdf_response.status_code}")
                else:
                    print(f"No PDF iframe found for: {title}")

            else:
                print(f"No PDF found for: {title}")
        except Exception as e:
            print(f"Failed to download PDF for: {link}, Error: {e}")

# 关闭 WebDriver
driver.quit()