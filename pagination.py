
class Paginate:
    def __init__(self, entries:list, per_page:int, numbered=True) -> None:
        self.entries  = entries
        self.per_page = per_page
        self.numbered = numbered

    def get_page(self, page:int):
        entries   = self.entries
        per_page  = self.per_page
        numbered = self.numbered
        tot_pages = (len(entries)-len(entries)%per_page)//per_page+1 if len(entries)%per_page!=0 else len(entries)//per_page
        if page>tot_pages:page=tot_pages
        start_index = (page-1)*per_page
        end_index = start_index+per_page
        if end_index>len(entries):end_index=len(entries)
        entries_on_page = entries[start_index:end_index]
        return_str = ""
        for entry in entries_on_page:
            if numbered:
                return_str = return_str + f"**{entries.index(entry)+1}.** {entry}\n"
            else:return_str = return_str + f"{entry}\n"
        return return_str
    
    def page_count(self):
        entries   = self.entries
        per_page  = self.per_page
        return (len(entries)-len(entries)%per_page)//per_page+1 if len(entries)%per_page!=0 else len(entries)//per_page

