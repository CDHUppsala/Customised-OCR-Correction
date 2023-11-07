import compare_to_word_lists

def run():
    main_output = "nonsense_statistics"
    main_output_text = "nonsense_processed_text"
    distance = 1
    
    replaces = [("b", "h"), ("à", "å"), ("the", "tbc"), ("a", "å"), ("a", "ä"), ("o", "ö"), ("m", "rn"), ("li", "h"), ("A", "Å"), ("I", "J"), ("ma", "rna"), ("mw", "rne"), ("Il", "H"), ("h", "n"), ("aa", "å"), ("ö", "o"), ("O", "Ö"), ("h", "b"), ("c", "e"), ("S", "å")]

    compare_to_word_lists.compare_folder(corpus_folder="nonsense-texts",
     terminologies_file_name="demo-word-lists.txt",
     output_filename="nonsense-statistics.txt",
     main_output=main_output,
     main_output_text=main_output_text,
     periodical="nonsense",
     language="sv",
     distance=distance,
     replacers=replaces,
     one_letter_words = ["m", "g", "a", "i", "å", "ä", "ö"],
     freq_dict_window=3,
     is_known_compound_function = compare_to_word_lists.is_known_compound_swedish,
     to_exclude_from_terminology = [],
     min_freq_in_OCRed_corpus_to_replace=2,
     not_to_correct=[])
     
run()
