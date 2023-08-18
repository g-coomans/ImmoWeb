import os
import requests

class ImmoCollecterTools: 
    @staticmethod
    def _get_data_from_tree(searchKey, data):
        # Extract data following the search Key in the list 'searchKey' in 'data' tree
        # can navigate in list or in dictionnary
        # example :
        # searchKey = ['price', 'mainValue']
        # data = ['price' : ['mainValue' : 500, 'lastValue' : 150], 'date' : 01/01/2022]
        # getDataFromTree returns 500
        if len(searchKey) == 0:
            return ""
        try:
            if len(searchKey) > 1:
                if isinstance(searchKey[0], int):
                    return ImmoCollecterTools._get_data_from_tree(searchKey[1:], data[0])
                elif isinstance(searchKey[0], str):
                    return ImmoCollecterTools._get_data_from_tree(searchKey[1:], data.get(searchKey[0], None))
            elif len(searchKey) == 1 :
                if isinstance(searchKey[0], int):
                    return data[searchKey[0]]
                elif isinstance(searchKey[0],str):
                    return data.get(searchKey[0], None)
        except (TypeError, AttributeError) as error:
            #print(f'Can\'t extract {searchKey}')
            return None

    @staticmethod
    def extract_data_house(house, conversion):
        dataAd = {}
        for key, value in conversion.items():
            dataAd[key] = ImmoCollecterTools._get_data_from_tree(value, house)
        return dataAd

    @staticmethod
    def download_pictures(urls, dowmload_dir):
        if not os.path.exists(dowmload_dir):
            os.mkdir(dowmload_dir)
        local_urls = []
        for pic_url in urls:
            pic_file_name = pic_url.split('/')[-1].split('?')[0]
            local_pic_path = os.path.join(dowmload_dir, pic_file_name)
            local_urls.append(local_pic_path)
            if os.path.exists(local_pic_path):
                continue
            try:
                with requests.get(pic_url, stream=True) as r:
                    if r.status_code != 200:
                        print(f"Error downloading pic: {pic_url} : {str(r)}")
                    with open(local_pic_path, 'wb') as f:
                        f.write(r.content)
            except Exception as e:
                print(f"Error downloading pic: {pic_url} : {str(e)}")
        return ",".join(local_urls)