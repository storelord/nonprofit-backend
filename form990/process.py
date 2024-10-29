#!/usr/bin/env python3

import os
import json
import re
import csv
import copy
import pgeocode
import xml.etree.ElementTree as ET

def calculate_distance_between_zip_codes(zip_code1, zip_code2=46556, country='us'):
    # Initialize the GeoDistance object for the specified country
    dist = pgeocode.GeoDistance(country)
    
    # Calculate the distance between the two zip codes
    distance = dist.query_postal_code(zip_code1, zip_code2)
    
    return distance
import heapq
class ScoreObject:
    def __init__(self, obj_id, score):
        self.obj_id = obj_id
        self.score = score

    def __lt__(self, other):
        return self.score < other.score  # Change comparison to create a min-heap

    def __repr__(self):
        return f"ScoreObject(id={self.obj_id}, score={self.score})"

class LimitedHeap:
    def __init__(self, max_size):
        self.max_size = max_size
        self.heap = []

    def add(self, score_obj):
        heapq.heappush(self.heap, score_obj)
        if len(self.heap) > self.max_size:
            self.remove_smallest()  # Remove the smallest element

    def remove_smallest(self):
        if self.heap:
            heapq.heappop(self.heap)  # Removes the smallest element (root of the min-heap)

    def current_size(self):
        return len(self.heap)

    def get_heap(self):
        return list(self.heap)
score_heap = LimitedHeap(max_size=1000)

def escape_special_characters(text):
  try:
    return text.replace('"', '\\"').replace("'", "\\'")
  except (ValueError, TypeError, AttributeError):
    return ''
  # return re.escape(text)
def ensure_number(arg):
  try:
    return int(arg)
  except (ValueError, TypeError):
    return 0


all_top_keys = set({'SalesOfInventoryList', 'OtherNotesLoansRcvblLongSch', 'TransfersFrmControlledEntities', 'LegalFeesSchedule', 'OtherIncreasesSchedule', 'AffiliateListing', 'GainLossSaleOtherAssetsSch', 'IRS4562', 'IRS990EZ', 'TransferPrsnlBnftContractsDecl', 'ReasonableCauseExplanation', 'AppliedToPriorYearElection', 'OtherProfessionalFeesSchedule', 'EmployeeCompensationExpln', 'IRS990ScheduleM', 'AffiliatedGroupAttachment', 'DistributionFromCorpusElection', 'IRS990ScheduleC', 'BorrowedFundsElection', 'IRS8827', 'AmortizationSchedule', 'InvestmentsLandSchedule2', 'IRS8949', 'IRS3800', 'GeneralExplanationAttachment', 'ReductionExplanationStatement', 'IRS990ScheduleE', 'IRS4136', 'CompensationExplanation', 'IRS990ScheduleG', 'OtherIncomeSchedule2', 'InvestmentsCorpBondsSchedule', 'SubstantialContributorsSch', 'AffiliatedGroupSchedule', 'ExpenditureResponsibilityStmt', 'IRS990ScheduleH', 'IRS990ScheduleB', 'IRS990ScheduleL', 'MortgagesAndNotesPayableSch', 'ActyNotPreviouslyRptExpln', 'OtherAssetsSchedule', 'IRS990ScheduleO', 'IRS1041ScheduleD', 'AllOthProgRltdInvestmentsSch', 'IRS990ScheduleA', 'CashDistributionExplnStmt', 'InvestmentsCorpStockSchedule', 'OtherLiabilitiesSchedule', 'IRS990ScheduleD', 'IRS990ScheduleR', 'TaxUnderSection511Statement', 'InvestmentsGovtObligationsSch', 'CashDeemedCharitableExplnStmt', 'ContractorCompensationExpln', 'IRS990ScheduleJ', 'OtherDecreasesSchedule', 'IRS990TScheduleA', 'IRS990ScheduleK', 'DepreciationSchedule', 'LoansFromOfficersSchedule', 'AccountingFeesSchedule', 'IRS1120ScheduleD', 'ExplanOfLegisPoliticalActvts', 'ExplnOfNonFilingWithAGStmt', 'OtherNotesLoansRcvblShortSch2', 'IRS2439', 'DissolutionStmt', 'IRS990ScheduleF', 'AveragingAttachment', 'IRS8801', 'IRS990PF', 'LiquidationExplanationStmt', 'InvestmentsOtherSchedule2', 'IRS990ScheduleI', 'TransfersToControlledEntities', 'OtherExpensesSchedule', 'IRS990ScheduleN', 'IRS990', 'TaxesSchedule', 'IRS1041ScheduleI', 'OtherReceivablesOfficersSch', 'LandEtcSchedule2', 'IRS990T'})

global_example = dict()
most_officers = [0]
org_id = [0]
grant_id = [0]
filehandlers = {}

def write_organization_plus(id, file_path, is_foundation, ein, name, city, state, zip, phone, officer_name, officer_title, officer_phone, revenue, CYTotalRevenueAmt, CYContributionsGrantsAmt, CYRevenuesLessExpensesAmt, AllOtherContributionsAmt, TotalContributionsAmt, TotalProgramServiceExpensesAmt, DonatedServicesAndUseFcltsAmt, GrossReceiptsAmt, CYProgramServiceRevenueAmt, SummaryOfDirectChrtblActyGrp, Desc, MissionDesc, ActivityOrMissionDesc, SupplementalInformationDetail, summary):
    if False:
        if 'organizations' not in filehandlers:
            filehandlers['organizations'] = open('nonprofits3.tsv', 'w+')
            filehandlers['organizations'].write(
                "id\tsource\tyear\tfile_path\tis_foundation\tein\tname\tcity\tstate\tzip\tphone\tofficer_name\tofficer_title\tofficer_phone\trevenue\tCYTotalRevenueAmt\tCYContributionsGrantsAmt\tCYRevenuesLessExpensesAmt\tAllOtherContributionsAmt\tTotalContributionsAmt\tTotalProgramServiceExpensesAmt\tDonatedServicesAndUseFcltsAmt\tGrossReceiptsAmt\tCYProgramServiceRevenueAmt\tSummaryOfDirectChrtblActyGrp\tDesc\tMissionDesc\tActivityOrMissionDesc\tSupplementalInformationDetail\tSummary\n"
            )
        # if state == 'IN':
        fh = filehandlers['organizations']
        revenue = ensure_number(revenue)
        escaped_name = escape_special_characters(name)
        escaped_officer_name = escape_special_characters(officer_name)
        escaped_officer_title = escape_special_characters(officer_title)
        escaped_summary = escape_special_characters(SummaryOfDirectChrtblActyGrp)
        escaped_desc = escape_special_characters(Desc)
        escaped_mission_desc = escape_special_characters(MissionDesc)
        escaped_activity_or_mission_desc = escape_special_characters(ActivityOrMissionDesc)
        escaped_supplemental_information_detail = escape_special_characters(SupplementalInformationDetail)
        escaped_summary = escape_special_characters(summary)
        fh.write(
            f"{id}\t990Form\t2023\t{file_path}\t{is_foundation}\t{ein}\t{escaped_name}\t{city}\t{state}\t{zip}\t{phone}\t{escaped_officer_name}\t{escaped_officer_title}\t{officer_phone}\t{revenue}\t{CYTotalRevenueAmt}\t{CYContributionsGrantsAmt}\t{CYRevenuesLessExpensesAmt}\t{AllOtherContributionsAmt}\t{TotalContributionsAmt}\t{TotalProgramServiceExpensesAmt}\t{DonatedServicesAndUseFcltsAmt}\t{GrossReceiptsAmt}\t{CYProgramServiceRevenueAmt}\t{escaped_summary}\t{escaped_desc}\t{escaped_mission_desc}\t{escaped_activity_or_mission_desc}\t{escaped_supplemental_information_detail}\t{escaped_summary}\n"
        )

def write_organization(id, file_path, ein, name, city, state, zip, phone, officer_name, officer_title, officer_phone, revenue, mission):
    if False:
      if 'organizations' not in filehandlers:
          filehandlers['organizations'] = open('nonprofits.tsv', 'w+')
          filehandlers['organizations'].write(f"id\tsource\tyear\tfile_path\tein\tname\tcity\tstate\tzip\tphone\tofficer_name\tofficer_title\tofficer_phone\trevenue\tdescription\n")
      fh = filehandlers['organizations']
      # if state == 'IN':
      # if mission[0] == "'":
      #     mission = mission[1:]
      revenue = ensure_number(revenue)
      escaped_name = escape_special_characters(name)
      escaped_mission = escape_special_characters(mission)
      escaped_officer_name = escape_special_characters(officer_name)
      escaped_officer_title = escape_special_characters(officer_title)
      
      fh.write(f"{id}\t990Form\t2023\t{file_path}\t{ein}\t{escaped_name}\t{city}\t{state}\t{zip}\t{phone}\t{escaped_officer_name}\t{escaped_officer_title}\t{officer_phone}\t{revenue}\t{escaped_mission}\n")

def write_grant(id, ein, mission, granted_amt, granted_purpose, recipient_ein, recipient_name, recipient_city, recipient_state, recipient_zip):
    if True:
      if 'grants' not in filehandlers:
          filehandlers['grants'] = open('grants.tsv', 'w+')
          filehandlers['grants'].write(f"id\tsource\tyear\tdonor_ein\tmission\trecipient_ein\trecipient_name\trecipient_city\trecipient_state\trecipient_zip\tgranted_amount\tgranted_purpose\n")
      fh = filehandlers['grants']
      escaped_mission = escape_special_characters(mission)
      escaped_recipient_name = escape_special_characters(recipient_name)
      escaped_granted_purpose = escape_special_characters(granted_purpose)
      fh.write(f"{id}\t990Form\t2023\t{ein}\t{escaped_mission}\t{recipient_ein}\t{escaped_recipient_name}\t{recipient_city}\t{recipient_state}\t{recipient_zip}\t{granted_amt}\t{escaped_granted_purpose}\n")

# fh3 = open('revenues1.tsv', 'w+')
# def write_revenue(ein, name, revenue):
#     fh3.write(f"{ein}\t{name}\t{revenue}\n")


def merge_objects(a, b, depth=0):
    # 'a' needs to already be a dict
    for key in b:
        if key not in a:
            if isinstance(b[key], dict):
                a[key] = {}
                merge_objects(a[key], b[key], depth+1)
            else:
                a[key] = b[key]
        else:
            if isinstance(b[key], dict):
                if not isinstance(a[key], dict):
                    a[key] = {}
                merge_objects(a[key], b[key], depth+1)
            else:
                a[key] = b[key]
counts = [0, 0, 0]
grant_info = { 'total_private_grants': 0, 'total_private_granted_amount': 0, 'total_foundations': 0, 'total_public_grants': 0, 'total_public_granted_amount': 0, 'total_grantmakers': 0, 'foundation_eins': set() }

def parse_xml(file_path):
    has_mission = False
    is_foundation = False
    SummaryOfDirectChrtblActyGrp = Desc = MissionDesc = ActivityOrMissionDesc = SupplementalInformationDetail = ""
    interesting_numbers = {}
    interesting_values = {}
    revenue = None
    officer_name = officer_title = officer_phone = ''
    counts[0] += 1
    ein = "--------"
    nonprofit_name = ""
    """Parse XML file and convert to JSON-like structure."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Convert XML to a dictionary and remove namespace prefixes
        xml_dict = xml_to_dict(root)
        xml_dict_no_namespace = remove_namespace(xml_dict)

        # Print the JSON-like structure (pretty printed)
        # print(f'Contents of {file_path}:')
        if 'ReturnHeader' not in xml_dict_no_namespace:
            print(json.dumps(xml_dict_no_namespace, indent=2))
            print('^ No ReturnHeader')
            return
        return_header = xml_dict_no_namespace['ReturnHeader']
        # print(json.dumps(return_header, indent=2))
        nonprofit_name = return_header.get("Filer", {}).get("BusinessName", {}).get("BusinessNameLine1Txt", "Unknown")
        try:
            ein = return_header["Filer"]["EIN"]
        except KeyError:
            ein = "########"
        phone = return_header.get('Filer', {}).get('PhoneNum', '')
        address = return_header.get('Filer', {}).get("USAddress", {})
        city = address.get("CityNm", "")
        state = address.get("StateAbbreviationCd", "")
        zip = address.get("ZIPCd", "")

        if 'BusinessOfficerGrp' in return_header:
            if 'PersonNm' in return_header['BusinessOfficerGrp']:
                officer_name = return_header['BusinessOfficerGrp']['PersonNm']
            if 'PersonTitleTxt' in return_header['BusinessOfficerGrp']:
                officer_title = return_header['BusinessOfficerGrp']['PersonTitleTxt']
            if 'PhoneNum' in return_header['BusinessOfficerGrp']:
                officer_phone = return_header['BusinessOfficerGrp']['PhoneNum']


        return_data = xml_dict_no_namespace['ReturnData']
        officers = programs = []
        if "IRS990EZ" in return_data:
            # print('')
            # print('')
            # print('____________________________________________________________________')
            # print(nonprofit_name + " (" + ein + ") - " + business_officer_name + " {" + business_officer_title + "}")

            prefix = '\t'
            # merge_objects(global_example, xml_dict_no_namespace)
            irs990Ez = return_data["IRS990EZ"]

            interesting_numbers = ['GrossReceiptsAmt', 'ContributionsGiftsGrantsEtcAmt', 'ProgramServiceRevenueAmt', 'MembershipDuesAmt', 'InvestmentIncomeAmt', 'CostOrOtherBasisExpenseSaleAmt', 'GainOrLossFromSaleOfAssetsAmt', 'FundraisingGrossIncomeAmt', 'SpecialEventsDirectExpensesAmt', 'SpecialEventsNetIncomeLossAmt', 'GrossSalesOfInventoryAmt', 'CostOfGoodsSoldAmt', 'GrossProfitLossSlsOfInvntryAmt', 'OtherRevenueTotalAmt', 'TotalRevenueAmt', 'FeesAndOtherPymtToIndCntrctAmt', 'OccupancyRentUtltsAndMaintAmt', 'PrintingPublicationsPostageAmt', 'OtherExpensesTotalAmt', 'TotalExpensesAmt', 'ExcessOrDeficitForYearAmt', 'NetAssetsOrFundBalancesBOYAmt', 'NetAssetsOrFundBalancesEOYAmt', 'TotalProgramServiceExpensesAmt', 'GrantsAndSimilarAmountsPaidAmt', 'SaleOfAssetsGrossAmt', 'GamingGrossIncomeAmt', 'LoansToFromOfficersAmt']
            interesting_values = {}
            for field in interesting_numbers:
                value = 0
                if field in irs990Ez:
                    value = int(float(irs990Ez[field]))
                    interesting_values[field] = value
                    # if value != 0:
                    #     print(f"{prefix}{value:>8,} === {field}")
                interesting_values[field] = value

            interesting_ranges = ['CashSavingsAndInvestmentsGrp', 'LandAndBuildingsGrp', 'OtherAssetsTotalDetail', 'Form990TotalAssetsGrp', 'SumOfTotalLiabilitiesGrp', 'NetAssetsOrFundBalancesGrp']
            for key in interesting_ranges:
                if key in irs990Ez:
                    range = irs990Ez[key]
                    if range and 'BOYAmt' in range and 'EOYAmt' in range:
                        for range_key in ['BOYAmt', 'EOYAmt']:
                            value = int(float(irs990Ez[key][range_key]))
                            interesting_values[key+range_key] = value
                            # if value != 0:
                            #     print(f"{prefix}{value:>8,} === {key+range_key}")

            # print(json.dumps(interesting_values, indent=2))
            # print("\n\n\n\n\n")
            score = interesting_values['InvestmentIncomeAmt'] + interesting_values['ExcessOrDeficitForYearAmt']

            # score_heap.add(ScoreObject(file_path, score))
            # print(file_path, score)


            # interesting_strings = ['WebsiteAddressTxt', 'PrimaryExemptPurposeTxt']
            # for field in interesting_strings:
            #     if field in irs990Ez:
            #         print(f"{prefix}{irs990Ez[field]} === {field}")
            # print('')
            # print(json.dumps(irs990Ez, indent=2))



            if 'ProgramSrvcAccomplishmentGrp' in irs990Ez:
                for program in irs990Ez['ProgramSrvcAccomplishmentGrp']:
                    programs.append(program)
            if 'OfficerDirectorTrusteeEmplGrp' in irs990Ez:
                if type(irs990Ez['OfficerDirectorTrusteeEmplGrp']) is list:
                    for officer in irs990Ez['OfficerDirectorTrusteeEmplGrp']:
                        if float(officer['CompensationAmt']) > 0:
                            officers.append(officer)
                else:
                    officer = irs990Ez['OfficerDirectorTrusteeEmplGrp']
                    if float(officer['CompensationAmt']) > 0:
                        officers.append(officer)

            revenue = total_revenue = interesting_values["TotalRevenueAmt"]
            # total_expenses = interesting_values["TotalExpensesAmt"]
            # net_revenue = interesting_values["ExcessOrDeficitForYearAmt"]
            
            # last_officer_count = most_officers[0]
            most_officers[0] = max(len(officers), most_officers[0])
            # if len(officers) > last_officer_count:
            #     print(nonprofit_name + " (" + ein + ") - " + business_officer_name + " {" + business_officer_title + "}")
            #     # print(json.dumps(officers, indent=2))
            #     print(json.dumps(xml_dict_no_namespace, indent=2))
            #     print(f"{prefix}Net Revenue: {total_revenue:>7,} - {total_expenses:>7,} = {net_revenue:>7,}")

            # 5 year trends (return_data['IRS990ScheduleA'])
            # return_detail['IRS990ScheduleG']['FundraisingEventInformationGrp']
            # return_detail['CompensationExplanation']
            # return_detail['IRS990ScheduleN'] going out of business or selling 25% of assets
            # IRS990ScheduleC Lobying
            # IRS990ScheduleL transactions with disqualified persons

            # print(f"{prefix}Net Revenue: {total_revenue:>7,} - {total_expenses:>7,} = {net_revenue:>7,}")
        
        if "IRS990" in return_data:
            irs990 = return_data['IRS990']
            interesting_numbers = ['CYTotalRevenueAmt', 'CYContributionsGrantsAmt', 'CYRevenuesLessExpensesAmt', 'AllOtherContributionsAmt', 'TotalContributionsAmt', 'TotalProgramServiceExpensesAmt', 'DonatedServicesAndUseFcltsAmt', 'GrossReceiptsAmt', 'CYProgramServiceRevenueAmt']
            interesting_values = {}
            for field in interesting_numbers:
                value = 0
                if field in irs990:
                    value = int(float(irs990[field]))
                    interesting_values[field] = value
                    # if value != 0:
                    #     print(f"{prefix}{value:>8,} === {field}")
                interesting_values[field] = value

            # print(json.dumps(interesting_values, indent=2))
            # print(json.dumps(irs990, indent=2))
            # print("\n\n\n\n\n")

            if 'CYTotalRevenueAmt' in interesting_values:
                revenue = interesting_values["CYTotalRevenueAmt"]
            if "RevenueAmt" in irs990:
                revenue = int(float(irs990["RevenueAmt"]))
            # print('---')

            Desc = irs990.get("Desc", "") # This is a Christian school in the Philipines. Educational services for a poverty striken community. Cost of school build and operations for 2022
            MissionDesc = irs990.get("MissionDesc", "") # Christian school in the Philipines

            ActivityOrMissionDesc = irs990.get("ActivityOrMissionDesc", "") # THE SPECIFIC PURPOSES OF THIS CORPORATION IS TO PROMOTE THE GENERAL WELFARE AND PROGRESS OF ALL PEOPLE, SUPPORTED BY MORAL & MATERIAL MEANS THAT WILL CONTRIBUTE TO THE ENHANCEMENT OF EDUCATION & SOCIAL PROGRESS OF THE USA & MACEDONIA,GREECE. THIS NONPROFIT WILL PRESERVE, ENHANCE AND DISSEMINATE THE GREEK MACEDONIAN CULTURE IN THE USA.

            counts[2] += 1
            # print(counts)
            # if counts[2] == 3:
            #     print(json.dumps(irs990, indent=2))
            #     exit(0)
            # else:
            #     print('No mission')


        # score_heap.add(ScoreObject(file_path, grants_by_1org))

        # if "IRS990T" in return_data:
        #     irs990t = return_data['IRS990T']
        #     print(json.dumps(irs990t, indent=2))

        # irs990sA = return_data.get("IRS990ScheduleA", {})
        # irs990sB = return_data.get("IRS990ScheduleB", {})
        
        if "IRS990ScheduleC" in return_data:
          irs990sC = return_data.get("IRS990ScheduleC", {})
          if irs990sC:
            details = irs990sC.get("SupplementalInformationDetail", {})
            if not isinstance(details, list):
              details = [details]
            explanations = []
            for detail in details:
              explain_text = detail.get("ExplanationTxt", "")
              if explain_text and len(explain_text)>4:
                explanations.append(explain_text)
            SupplementalInformationDetail = ", ".join(explanations)
        

        # irs990sD = return_data.get("IRS990ScheduleD", {})
        # # Google Ad contributions would probably be here.
        # if irs990sD != {}:
        #   print(json.dumps(irs990sD, indent=2))
        #   print("\n\n\n\n\n")

        summary = MissionDesc
        if not summary:
            summary = ActivityOrMissionDesc
        if not summary:
            summary = SupplementalInformationDetail
        if not summary:
            summary = Desc


        # irs990sE = return_data.get("IRS990ScheduleE", {})
        # irs990sG = return_data.get("IRS990ScheduleG", {})
        if "IRS990ScheduleI" in return_data:
          irs990sI = return_data.get("IRS990ScheduleI", {})
          if irs990sI:
            table = irs990sI.get('RecipientTable', [])
            if not isinstance(table, list):
                table = [table]
            for grant_or_contribution in table:
              if grant_or_contribution:
                recipient_ein = grant_or_contribution.get('RecipientEIN', "")
                recipient_name = grant_or_contribution.get('RecipientBusinessName', {}).get("BusinessNameLine1Txt", "Unknown")
                recipient_city = grant_or_contribution.get('RecipientUSAddress', {}).get("CityNm", "")
                recipient_state = grant_or_contribution.get('RecipientUSAddress', {}).get("StateAbbreviationCd", "")
                recipient_zip = grant_or_contribution.get('RecipientUSAddress', {}).get("ZIPCd", "")
                granted_purpose = grant_or_contribution.get('PurposeOfGrantTxt', '')
                granted_amt = grant_or_contribution.get('CashGrantAmt', -1)
                # write_public_granted(ein, nonprofit_name, recipient_ein, recipient_name, recipient_city, recipient_state, recipient_zip, granted_purpose, granted_amt)
                # recipient_info = {
                #     "name": recipient_name,
                #     "city": recipient_city,
                #     "state": recipient_state,
                #     "zip": recipient_zip
                # }
                # recipient_data = json.dumps(recipient_info)
                grant_id[0] += 1
                write_grant(grant_id[0], ein, summary, granted_amt, granted_purpose, recipient_ein, recipient_name, recipient_city, recipient_state, recipient_zip)
              else:
                print(json.dumps(table, indent=2))
        # irs990sI = return_data.get("IRS990ScheduleJ", {})
        # irs990sO = return_data.get("IRS990ScheduleO", {})
        # irs990sR = return_data.get("IRS990ScheduleR", {})
        org_id[0] += 1
        # write_organization(org_id[0], file_path, ein, nonprofit_name, city, state, zip, phone, officer_name, officer_title, officer_phone, revenue, mission + '.')
        CYTotalRevenueAmt = interesting_values.get('CYTotalRevenueAmt', 0)
        CYContributionsGrantsAmt = interesting_values.get('CYContributionsGrantsAmt', 0)
        CYRevenuesLessExpensesAmt = interesting_values.get('CYRevenuesLessExpensesAmt', 0)
        AllOtherContributionsAmt = interesting_values.get('AllOtherContributionsAmt', 0)
        TotalContributionsAmt = interesting_values.get('TotalContributionsAmt', 0)
        TotalProgramServiceExpensesAmt = interesting_values.get('TotalProgramServiceExpensesAmt', 0)
        DonatedServicesAndUseFcltsAmt = interesting_values.get('DonatedServicesAndUseFcltsAmt', 0)
        GrossReceiptsAmt = interesting_values.get('GrossReceiptsAmt', 0)
        CYProgramServiceRevenueAmt = interesting_values.get('CYProgramServiceRevenueAmt', 0)

        grants_by_1org = 0
        if "IRS990PF" in return_data:
            irs990pf = return_data['IRS990PF']
            # print('______________________')
            # print(json.dumps(xml_dict_no_namespace, indent=2))
            # print('^^^^^^^^^^^^^^^^^^^^^^')
            if irs990pf is not None:
              # print(json.dumps(irs990pf, indent=2))
              # print('--')
              try:
                SummaryOfDirectChrtblActyGrp = irs990pf.get('SummaryOfDirectChrtblActyGrp', {}).get("Description1Txt", "") or ""
              except:
                 pass
              
              # analysis_of_revenue_and_expenses = irs990pf['AnalysisOfRevenueAndExpenses']
              # form990_pf_balance_sheet_grp = irs990pf['Form990PFBalanceSheetsGrp']
              # distributable_amount_grp = irs990pf['DistributableAmountGrp']
              # undistributed_income_grp = irs990pf['UndistributedIncomeGrp']
              if 'SupplementaryInformationGrp' in irs990pf:
                  supplementary_information_grp = irs990pf['SupplementaryInformationGrp']
                  # print(json.dumps(xml_dict_no_namespace, indent=2))
                  grant_info['total_foundations'] += 1

                  try:
                      for grant_or_contribution in supplementary_information_grp['GrantOrContributionPdDurYrGrp']:
                          # print(json.dumps(supplementary_information_grp, indent=2))
                          # recipient_ein = grant_or_contribution.get('RecipientEIN', "")
                          recipient_name = grant_or_contribution.get('RecipientBusinessName', {}).get("BusinessNameLine1Txt", "Unknown")
                          recipient_status = grant_or_contribution.get('RecipientFoundationStatusTxt', "Unknown")
                          recipient_city = grant_or_contribution.get('RecipientUSAddress', {}).get("CityNm", "")
                          recipient_state = grant_or_contribution.get('RecipientUSAddress', {}).get("StateAbbreviationCd", "")
                          recipient_zip = grant_or_contribution.get('RecipientUSAddress', {}).get("ZIPCd", "")
                          granted_purpose = grant_or_contribution.get('GrantOrContributionPurposeTxt', None)
                          granted_amt = grant_or_contribution.get('Amt', None)
                          # write_private_granted(ein, nonprofit_name, recipient_name, recipient_status, recipient_city, recipient_state, recipient_zip, granted_purpose, granted_amt)
                          # recipient_info = {
                          #     "name": recipient_name,
                          #     "city": recipient_city,
                          #     "state": recipient_state,
                          #     "zip": recipient_zip
                          # }
                          # recipient_data = json.dumps(recipient_info)
                          grant_id[0] += 1
                          grants_by_1org += 1
                          write_grant(grant_id[0], ein, summary, granted_amt, granted_purpose, '', recipient_name, recipient_city, recipient_state, recipient_zip)
                  except:
                      pass
                  # exit(0)
                  is_foundation = True                
            # return

        write_organization_plus(org_id[0], file_path, is_foundation, ein, nonprofit_name, city, state, zip, phone, officer_name, officer_title, officer_phone, revenue, CYTotalRevenueAmt, CYContributionsGrantsAmt, CYRevenuesLessExpensesAmt, AllOtherContributionsAmt, TotalContributionsAmt, TotalProgramServiceExpensesAmt, DonatedServicesAndUseFcltsAmt, GrossReceiptsAmt, CYProgramServiceRevenueAmt, SummaryOfDirectChrtblActyGrp, Desc, MissionDesc, ActivityOrMissionDesc, SupplementalInformationDetail, summary)


    except ET.ParseError as e:
        print(f'Error parsing XML file {file_path}: {str(e)}')

def remove_namespace(data):
    """Recursively remove namespace prefix from dictionary keys."""
    if isinstance(data, dict):
        return {
            key.split('}')[-1]: remove_namespace(value) 
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [remove_namespace(item) for item in data]
    else:
        return data

def xml_to_dict(element):
    """Convert XML element to a dictionary recursively."""
    if len(element) == 0:
        return element.text
    result = {}
    for child in element:
        child_data = xml_to_dict(child)
        if child.tag in result:
            if type(result[child.tag]) is list:
                result[child.tag].append(child_data)
            else:
                result[child.tag] = [result[child.tag], child_data]
        else:
            result[child.tag] = child_data
    return result

def traverse_folders(folder_path):
    processed_file_count = 0
    """Traverse through subfolders and parse XML files."""
    cnt = 0
    for dirpath, _, filenames in os.walk(folder_path):
        # print(dirpath)
        for filename in filenames:
            if filename.endswith('.xml'):
                file_path = os.path.join(dirpath, filename)
                # print(cnt, dirpath, filename, file_path)
                parse_xml(file_path)
                cnt += 1
        #     if cnt > 10000:
        #        break
        # if cnt > 10000:
        #     break

    print(cnt)
    # print(most_officers[0], 'paid officers in one nonprofit org')
    # print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    # print(json.dumps(global_example, indent=2))
    # grant_info['foundation_eins'] = len(grant_info['foundation_eins'])
    # print(json.dumps(grant_info, indent=2))

    # heap_elements = score_heap.get_heap()
    # sorted_elements = sorted(heap_elements, key=lambda x: -x.score)
    # sorted_result = [(obj.obj_id, obj.score) for obj in sorted_elements]

    # for obj_id, score in sorted_result:
    #   print(obj_id, score)


if __name__ == "__main__":
    # Specify the folder path to start the search
    folder_path = './'

    # Traverse through the folder and its subfolders to parse XML files
    traverse_folders(folder_path)
