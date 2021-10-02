try:
    import sys, os, logging
except:
    print("ExceptionERROR: cRecruitmentCriteria is missing fundamental packages (required: os, sys, logging, webbrowser).")

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) + "\\.site_packages\\riverpy\\")
    import config
    from collections import defaultdict
    sys.path.append(config.dir2oxl)
    import pandas as pd
except:
    print("ExceptionERROR: Missing RiverArchitect packages (required: /.site_packages/riverpy/).")


class RecruitmentCriteria:
    # Read recruitment criteria from file as a function of criteria name
    def __init__(self):
        # set location of recruitment criteria xlsx file
        self.recruitment_xlsx = config.xlsx_recruitment
        # populated by self.get_species()
        self.species_list = []
        # populated by self.get_common_names()
        self.common_name_list = []
        # populated by self.create_species_dictionary()
        self.species_dict = {}

        # parameter names in recruitment criteria workbook
        self.sd_start = 'Season start'
        self.sd_end = 'Season end'
        self.base_flow_start = 'Base flow period starts'
        self.bed_prep_period = 'Bed preparation period'
        self.taux_cr_fp = 'Prepared'
        self.taux_cr_pp = 'Partially prepared'
        self.rr_fav = 'Favorable rate'
        self.rr_stress = 'Stressful rate'
        self.rr_lethal = 'Lethal rate'
        self.elev_fav = 'Favorable elevation'
        self.elev_stress = 'Stressful elevation'
        self.elev_lethal = 'Lethal elevation'
        self.inund_fav = 'Favorable inundation'
        self.inund_stress = 'Stressful indunation'
        self.inund_lethal = 'Lethal inundation'

        # read recruitment sheet in recruitment criteria excel file to dataframe, first column assigned as index
        try:
            self.df = pd.read_excel(self.recruitment_xlsx, sheet_name='recruitment', index_col=0)
        except:
            print("ERROR: Could not find " + str(self.recruitment_xlsx))

        self.get_species()
        self.get_common_names()
        self.create_species_dict()

    def get_species(self):
        # iterate though columns in dataframe skipping 'UNITS' column
        self.species_list = []
        for col in self.df.columns[1:]:
            # adding each species column to self.species_list with 'UNITS' column
            species_df = self.df[[col, 'UNITS']]
            species_df.columns = ['VALUE', 'UNITS']
            self.species_list.append(species_df)
        return self.species_list

    def get_common_names(self):
        # iterate through each species in self.species_list
        self.common_name_list = []
        for species in self.species_list:
            # adding each species common name to self.common_name_list
            self.common_name_list.append(species.loc['Common name'][0])
        return self.common_name_list

    def create_species_dict(self):
        # create species dictionary with self.common_name_list as keys and self.species_list as values
        self.species_dict = dict(zip(self.common_name_list, self.species_list))

    def __call__(self, *args, **kwargs):
        print("Class Info: <type> = RecruitmentCriteria (%s)" % os.path.dirname(__file__))
        print(dir(self))


if __name__ == "__main__":
    rc = RecruitmentCriteria()
    print(rc)
