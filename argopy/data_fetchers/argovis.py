#!/bin/env python
# -*coding: UTF-8 -*-
#
# Argo data fetcher for Argovis.
#
# This is comprised of functions used to query Argovis api
# query functions either return dictionary objects or error messages.

access_points = ['wmo', 'profile', 'shape'] # query options available
exit_points = [ 'json', 'dataframe', 'xarray'] # outputs availably by data fetcher
dataset_ids = ['phy', 'bgc']

import pandas as pd
import xarray as xr
import requests
import pdb
import json
import os, sys
#sys.path.append(os.path.join(os.pardir, 'stores'))
from proto import ArgoDataFetcherProto
# sys.path.append('../..')
# import argopy
# from argopy.stores import httpstore

class ArgovisDataFetcher(ArgoDataFetcherProto):
    """
    Manage access to Argo data through Argovis
    """
    @staticmethod
    def urlopenjson(url):
        resp = requests.get(url)
        # Consider any status other than 2xx an error
        if not resp.status_code // 100 == 2:
            return "Error: Unexpected response {}".format(resp)
        return resp.json()

    # @staticmethod
    # def urlopenjson(url):
    #     with httpstore(timeout=120).open("https://argovis.colorado.edu/catalog/profiles/5904797_12") as of:
    #         return json.load(of)

    @staticmethod
    def filter_data_mode(profiles, data_mode):
        '''
        Parameters
        ----------
        profiles: list of dictionary from the 'get_' functions
        data_mode: valid strings for delayed, realtime, and adjusted are : 'D', 'R', 'A' respectively.

        Example
        -------
        from argovis import ArgovisDataFetcher
        adf = ArgovisDataFetcher()
        profiles = adf.get_platform_profiles(3900737)
        profiles = adf.filter_data_mode(profiles, 'A')
        '''
        profiles = [p for p in profiles if p['DATA_MODE'] == data_mode]
        return profiles

    @staticmethod
    def filter_qc(profiles, qc_key, qc_value):
        '''
        Filter either date_qc or position_qc values from profiles.
        Argovis does not inlcude position_qc of 3 or 4. 

        Parameters
        ----------
        profiles: list of dictionary from the 'get_' functions
        qc_key: valid strings include 'position_qc', 'date_qc'
        qc_value: valid digits: range from 0 to 9.
        Example
        -------
        from argovis import ArgovisDataFetcher
        adf = ArgovisDataFetcher()
        profiles = adf.get_platform_profiles(3900737)
        profiles = adf.filter_qc(profiles, 'date_qc', 2)
        '''
        profiles = [p for p in profiles if p[qc_key] == qc_value]
        return profiles

    @staticmethod
    def filter_variables(profiles, variable_keys):
        '''
        Filter from 'measurements' list such that only variable_keys remain

        Parameters
        ----------
        profiles: list of dictionary from the 'get_' functions
        qc_key: valid strings include 'position_qc', 'date_qc'
        qc_value: valid digits: range from 0 to 9.
        Example
        -------
        from argovis import ArgovisDataFetcher
        adf = ArgovisDataFetcher()
        profiles = adf.get_platform_profiles(3900737)
        profiles = adf.filter_variables(profiles, ['temp', 'psal'])
        '''
        for profile in profiles:
            for meas in profile['measurements']:
                for key in meas.keys():
                    if key in variable_keys:
                        del meas[key]
        return profiles

    @staticmethod
    def to_dataframe(profiles, measKey='measurements'):
        rows = []
        for profile in profiles:
            keys = [ x for x in profile.keys() if not x in ['measurements', 'bgcMeas']]
            meta_row = dict( (key, profile[key]) for key in keys)
            for row in profile[measKey]:
                row.update(meta_row)
                rows.append(row)
        df = pd.DataFrame(rows)
        return df

    def to_xarray(self, profiles):
        """ imput list of dictionarys and return a xarray Dataset """
        return self.to_dataframe(profiles).to_xarray()

    def get_profile(self, platform_number, cycle_number):
        '''
        Returns either a dictionary for one profile, or an error string.

        Parameters
        ----------
        platform_number: wmo float id.
        cycle_number: numer signifying the profile number for this particular platform

        Example
        -------
        from argovis import ArgovisDataFetcher
        adf = ArgovisDataFetcher()
        profile = adf.get_profile(3900737, 279)
        '''
        profile_number = str(platform_number) + '_' + str(cycle_number)
        url = 'https://argovis.colorado.edu/catalog/profiles/{}'.format(profile_number)
        profile = self.urlopenjson(url)
        return profile

    def get_profiles(self, profList, presRange=None):
        '''
        Parameters
        ----------
        profList: list of strings comprising profile numbers (ex 1900722_1)
        presRange (optional): list of two numbers formatted as [lowerPressure,upperPressure].
        Example
        -------
        from argovis import ArgovisDataFetcher
        adf = ArgovisDataFetcher()
        ids=['1900722_1','1900722_2']
        presRange=[0,20]
        profiles = adf.get_profiles(ids, presRange)

        '''
        url = 'https://argovis.colorado.edu/catalog/mprofiles/?ids='
        url += str(profList).replace(' ', '')
        if presRange:
            pressRangeQuery = '&presRange=' + str(presRange).replace(' ', '')
            url += pressRangeQuery
        profiles = self.urlopenjson(url)


    def get_platform_profiles(self, platform_number):
        '''
        Returns either a list of dictionary objects representing profile data from a platform, or an error string.

        Parameters
        ----------
        platform_number: wmo float id.

        Example
        -------
        from argovis import ArgovisDataFetcher
        adf = ArgovisDataFetcher()
        platformProfiles = adf.get_platform_profiles(3900737)
        '''
        url = 'https://argovis.colorado.edu/catalog/platforms/{}'.format(str(platform_number))
        platformProfiles = self.urlopenjson(url)
        return platformProfiles

    def get_selection_profiles(self, startDate, endDate, shape, presRange=None, bgcOnly=False, deepOnly=False, printUrl=True):
        '''
        Returns either a list of dictionary objects representing profile data, or an error string.

        Parameters
        ----------
        start date: str formatted as 'YYYY-MM-DD'
        end date: str formatted as 'YYYY-MM-DD'
        pressure range (optional): list of two numbers formatted as [lowerPressure,upperPressure].
        shape: a list of lists containing [lng, lat] coordinates. First and last coordinate should
        be equal.
        bgcOnly: boolean (optional) to filter out biogeochemical profiles
        deepOnly: boolean (optional)to filter out deep profiles (profiles that dive below 2000 dbar.)
        printURL: boolean (optional)
    

        Example
        -------
        shape = [[[168.6,21.7],[168.6,37.7],[-145.9,37.7],[-145.9,21.7],[168.6,21.7]]]
        startDate='2017-9-15'
        endDate='2017-9-30'
        presRange=[0,50]
        selectionProfiles = adf.get_selection_profiles(startDate, endDate, shape, presRange)
        '''
        url = 'https://argovis.colorado.edu/selection/profiles'
        url += '?startDate={}'.format(startDate)
        url += '&endDate={}'.format(endDate)
        url += '&shape={}'.format( str(shape).replace(' ', ''))
        if bgcOnly:
            url += '&bgcOnly=' + str(bgcOnly)
        if deepOnly:
            url += '&deepOnly=' + str(deepOnly)
        if presRange:
            pressRangeQuery = '&presRange=' + str(presRange).replace(' ', '')
            url += pressRangeQuery
        if printUrl:
            print(url)
        selectionProfiles = self.urlopenjson(url)
        return selectionProfiles

class Fetch_wmo(ArgovisDataFetcher):
    def init(self, WMO, CYC=[], presRange=None):
        self.WMO = WMO
        self.CYC = CYC
        self.presRange = presRange

        if isinstance(WMO, int):
            WMO = [WMO]  # Make sure we deal with a list
        if isinstance(CYC, int):
            CYC = np.array((CYC,), dtype='int')  # Make sure we deal with an array of integers
        if isinstance(CYC, list):
            CYC = np.array(CYC, dtype='int')  # Make sure we deal with an array of integers

        return self

    
    @staticmethod
    def make_profile_id(WMO, CYC):
        return wmo + '_' + cyc

    def generate_queries(self):
        '''
        determine which argovis query should be made: get_profile(), get_platform_profiles(),
        or get_profiles_by_id()
        '''
        if len(self.CYC) == 1: # profile
            # either get_profile or profiles
            profiles = self.get_profile(this.make_profile_id(self.WMO[0], self.CYC[0]))
        elif len(self.CYC) > 1:
            # get a list of profiles
            profIds = self.make_list_of_profiles()
            profiles = self.get_profiles(profIds, self.presRange)
        else:
            #get platforms
            profiles = self.get_platform_profiles(self.WMO)
        return fun
    
    def make_list_of_profiles(self):
        '''
        cartesian product of cycle number and wmo number
        '''
        profIds = [str(wmo) + '_' + str(cyc) for wmo in self.WMO for cyc for self.CYC]
        return profIds




class Fetch_box(ArgovisDataFetcher):
    def __init__(self, BOX)
        self lon_min

