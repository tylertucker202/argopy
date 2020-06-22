from argovis import ArgovisDataFetcher
import pandas as pd
import xarray as xr
import pdb

adf = ArgovisDataFetcher()
profile = adf.get_profile(3900737, 279)
assert not isinstance(profile, str)
df = adf.to_dataframe([profile])
assert isinstance(df, pd.core.frame.DataFrame)
assert df.shape[0] > 0
ds = adf.to_xarray([profile])
assert isinstance(ds, xr.core.dataset.Dataset)

profiles = adf.get_platform_profiles(3900737)
df = adf.to_dataframe(profiles)
assert isinstance(df, pd.core.frame.DataFrame)
assert df.shape[0] > 0
ds = adf.to_xarray(profiles)
assert isinstance(ds, xr.core.dataset.Dataset)

shape = [[[168.6,21.7],[168.6,37.7],[-145.9,37.7],[-145.9,21.7],[168.6,21.7]]]
startDate='2017-9-15'
endDate='2017-9-30'
presRange=[0,50]
selectionProfiles = adf.get_selection_profiles(startDate, endDate, shape, presRange)
df = adf.to_dataframe(selectionProfiles)
assert isinstance(df, pd.core.frame.DataFrame)
assert df.shape[0] > 0
ds = adf.to_xarray(selectionProfiles)
assert isinstance(ds, xr.core.dataset.Dataset)

# test deep and bgc filtering
startDate = '2020-06-08'
endDate = '2020-06-22'
presRange = [0, 50]
shape = [[[177.890625,-15.961329],[-179.648438,-40.313043],[-171.339988,-40.351859],[-163.094396,-39.799128],[-155.04674,-38.675436],[-147.304688,-37.020098],[-154.354757,-25.353216],[-160.136719,-13.410994],[-167.401361,-14.491287],[-174.729546,-15.346662],[-180,-15.785639],[-180,-15.785639],[177.890625,-15.961329]]]
bgcProfiles = adf.get_selection_profiles(startDate, endDate, shape, presRange, bgcOnly=True)
assert len(bgcProfiles) > 0
assert all([p['containsBGC'] for p in bgcProfiles])

deepProfiles = adf.get_selection_profiles(startDate, endDate, shape, presRange, bgcOnly=False, deepOnly=True)
assert len(deepProfiles) > 0
assert all([p['isDeep'] for p in deepProfiles])

# test filtering
profiles = adf.get_platform_profiles(3900737)
profiles_1 = adf.filter_qc(profiles, 'date_qc', 1)
assert len(profiles_1) > 0
profiles_2 = adf.filter_qc(profiles, 'date_qc', 2)
assert len(profiles_1) > len(profiles_2)

profiles = adf.get_platform_profiles(4901653) # missing a profile
profiles_1 = adf.filter_qc(profiles, 'position_qc', 1)
assert len(profiles) > len(profiles_1)
assert all([p['position_qc'] == 1 for p in profiles_1])
profiles_9 = adf.filter_qc(profiles, 'position_qc', 9)
assert len(profiles_1) > len(profiles_9)
assert all([p['position_qc'] == 9 for p in profiles_9])