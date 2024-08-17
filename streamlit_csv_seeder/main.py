import inspect
import os

import pandas as pd
import streamlit as st
from mimesis import BaseDataProvider, BaseProvider, Generic, Locale
from pydash import snake_case

STATUS_OPTION_LIST = ["Pending", "In-Review", "Approved", "Rejected", "Completed"]


class Status(BaseProvider):
	def status(self) -> str:
		return self.random.choice(STATUS_OPTION_LIST)


DEFUALT_METHOD_NAME = "word"
DEFUALT_ID_METHOD_NAME = "cid"
provider_class_list = []
provider_name_provider_dict = {}
method_name_method_dict = {}
method_name_list = []

ignore_provider_list = [BaseProvider(), BaseDataProvider()]
ignore_method_name_list = [
	method_name
	for provider in ignore_provider_list
	for method_name, method in inspect.getmembers(provider, predicate=inspect.ismethod)
	if not method_name.startswith("_")
]


def generate_mimesis_method_dict_for_locale(value):
	global provider_class_list
	global provider_name_provider_dict
	global method_name_method_dict
	global method_name_list

	generic = Generic(locale=value)

	# Registering the new provider
	generic.add_provider(Status)

	# generic = Generic(locale=Locale[value])
	# person = Person()
	# address = Address()
	# text = Text()

	# List of Mimesis providers to introspect
	# providers = [generic, person, address, text]
	provider_class_list = [generic]
	provider_name_provider_dict = {
		provider_name: provider
		for provider_class in provider_class_list
		for provider_name, provider in inspect.getmembers(provider_class)
	}

	method_name_method_dict = {
		method_name: method
		for provider in provider_name_provider_dict.values()
		for method_name, method in inspect.getmembers(provider, predicate=inspect.ismethod)
		if not method_name.startswith("_") and method_name not in ignore_method_name_list
	}
	method_name_list = list(method_name_method_dict.keys())


def get_csv_headers(filepath):
	df = pd.read_csv(filepath)
	return list(df.columns)


def get_method_name_for_header(header):
	method_name = DEFUALT_METHOD_NAME
	if header in method_name_list:
		method_name = header
	elif header in ["id", "uid"]:
		return DEFUALT_ID_METHOD_NAME
	else:
		for name in method_name_list:
			if header in name:
				method_name = name
				break
		if "id" in header:
			return DEFUALT_ID_METHOD_NAME

	return method_name


def generate_csv(header_selection_list, locale, no_of_records, headers, filename_with_extension):
	method_name_list = header_selection_list
	no_of_records = no_of_records
	headers = headers
	filename_with_extension = filename_with_extension
	filename, _ = os.path.splitext(filename_with_extension)
	records = []

	generate_mimesis_method_dict_for_locale(locale)
	for _ in range(no_of_records):
		record = {}
		for index, method_name in enumerate(method_name_list):
			method = method_name_method_dict.get(method_name, DEFUALT_METHOD_NAME)
			record[headers[index]] = method()
		records.append(record)

	df = pd.DataFrame(records)
	csv_path = f"temp/{no_of_records} Records of {filename} ({locale}).csv"
	df.to_csv(csv_path, index=False, encoding="utf-8")

	return df, csv_path


uploaded_csv_file = st.file_uploader("Choose a CSV File", type=["csv"])
if uploaded_csv_file is not None:
	with st.form("process_csv_upload"):
		generate_mimesis_method_dict_for_locale(Locale.EN)
		headers = get_csv_headers(uploaded_csv_file)
		filename_with_extension = os.path.basename(uploaded_csv_file.name)
		st.subheader("Select _Type_ of each Headers")
		dropdown_options = method_name_list
		header_selection_list = []

		column_count = 4
		colums = st.columns(column_count)
		for index, header in enumerate(headers):
			lower_header = snake_case(header)
			default_value = get_method_name_for_header(lower_header)
			options = [*dropdown_options]
			options.remove(default_value)
			with colums[index % column_count]:
				selectbox = st.selectbox(
					label=header,
					placeholder=default_value,
					options=[default_value, *options],
					key=lower_header,
				)
				header_selection_list.append(selectbox)

		no_of_records = st.number_input("No. of records to Generate", min_value=1)
		locale_options = [locale.value for locale in Locale]
		default_locale_value = Locale.EN.value
		locale_options.remove(default_locale_value)
		locale = st.selectbox(
			label="Choose the Locale",
			options=[default_locale_value, *locale_options],
		)
		generate_records_btn = st.form_submit_button("Generate Records")
	if generate_records_btn:
		df, csv_path = generate_csv(
			header_selection_list,
			locale,
			no_of_records,
			headers,
			filename_with_extension,
		)
		st.dataframe(df)
