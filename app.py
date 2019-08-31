import asyncio
from pyppeteer import launch

async def main(query, max_results=None):
    #output with scraped data
    output = []
    #launch browser and open page
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.goto('https://data.gov')
    #Enter input query
    input_selector = 'input#search-header'
    await page.type(input_selector, query)
    #click search button
    search_selector = 'button.search-submit.btn.btn-default' 
    await page.click(search_selector)

    #check results element
    new_results_selector = 'div.new-results'
    await page.waitForSelector(new_results_selector)
    results_data = await page.querySelectorEval(new_results_selector, "elem => elem.textContent")
    results_data = results_data.strip()

    #Get element needed to traverse to next page
    active_li_item_selector = '#content > div.row.wrapper > div > section:nth-child(1) > div.pagination.pagination-centered > ul > li.active > a'
    current_URI = await page.querySelectorEval(active_li_item_selector, "elem => elem.href")

    #Return empty list if invalid query
    if "No datasets" in results_data:
        return output
    else:
        #Get total number of available datasets
        total_datasets = int("".join(results_data.split(" ")[0].split(",")))
        #check how many results to return
        if max_results < total_datasets:
            total_datasets = max_results

        #scrape till you get number of results specified
        while len(output) < total_datasets:
            #open next page
            if len(output) != 0:
                current_URI_componenets = current_URI.split("=")
                next_URI_page = str(int(current_URI_componenets[-1]) + 1)
                current_URI_componenets = current_URI_componenets[:-1] + [next_URI_page]
                current_URI =  "=".join(current_URI_componenets)
                await page.goto(current_URI)

            #data div element 
            current_results_selector = 'div.dataset-content'
            await page.waitForSelector(current_results_selector)
            all_div_items = await page.querySelectorAll(current_results_selector)

            #check how much more data needs to be added
            nodes_to_add = total_datasets - len(output) 
            nodes_on_current_page = []

            #for all child elements populate data list
            for idx, element in enumerate(all_div_items):
                child_element_list = await page.evaluate('''(element) => [...element.children].map(child => child.getAttribute('class'))''',element)
                child_text_contents = await page.evaluate('''(element) => [...element.children].map(child => child.textContent)''',element)
                print('------------')
                child_node = {
                            'organization_name': '',
                            'data_formats':[],
                            'dataset_name': ''
                }
                #check if data attribute exists in element
                for idx, prop in enumerate(child_element_list):
                    if prop == 'organization-type-wrap':
                        child_node['organization_name'] = child_text_contents[idx].strip()
                    elif prop == 'dataset-heading':
                        child_node['dataset_name'] = child_text_contents[idx].strip().split('\n')[0]
                    elif prop == 'dataset-resources unstyled':
                        child_node['data_formats'] = [data_format for data_format in child_text_contents[idx].strip().replace("\n", '').split(' ') if data_format != '']
                print(child_node)
                nodes_on_current_page.append(child_node)
            
            #add data to main output
            if nodes_to_add >= len(nodes_on_current_page):
                output += nodes_on_current_page
            else:
                output += nodes_on_current_page[:nodes_to_add]
    #close browser
    await browser.close()
    print(len(output))
    return output

if __name__ == '__main__':
    query = 'Health'
    max_data = 20
    asyncio.get_event_loop().run_until_complete(main(query, max_data))

