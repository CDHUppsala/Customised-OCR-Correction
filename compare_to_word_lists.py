import glob
import os
import re
import copy
import string
import math
import matplotlib.pyplot as plt
from spellchecker import SpellChecker
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer
from nltk.metrics import edit_distance


dividers = [".", ",", "!", "?", ":", "(", ")", ";", "„", '"', ":", ":","'", "‘", "»", "«", "}", "{", "*", '”', "[", "]", "•", "=",'”', "—•", "^", "'", "/", "'", "“", "„"]
   
letters = list(string.ascii_lowercase) + list(string.ascii_uppercase) + ["ü", "Ü", "å", "Å", "ä", "Ä", "ö", "Ö", "é", "É"]


default_replacers = [("II", "ll"), ("c", "e"), ("I", "i"), ("11", "ll"), ("11", "ti"), ("I", "l"), ("i", "l"), ("/J", "H"), ("Hl", "H"), ("il", "it"), ("HI", "H"), ("ll", "H"), ("Tc", "He"), ("1l", "H"), ("Il", "H"), ("ci", "ch"), ("U", "Ü"), ("Tl", "H"), ("pll", "pfl"), ("o", "a"), ("ll", "fl"), ("Sl", "St"), ("Ä", "A"), ("rl", "rt"), ("ll","li"), ("J", "I"), ("li", "ti"), ("f", "t"), ("il", "H"), ("Ie", "He"), ("ä", "a"), ("a", "ä"), ("EJ", "e"), ("l", "t"), ("in", "m"), ("Ilc", "He"), ("IH", "H"), ("II", "H"), ("Ll", "H"), ("d", "ch"), ("1", "l"), ("l", "1"), ("1", "t"), ("di", "ch"), ("ci-", "ch"), ("HI", "H"), ("i", "f"), ("-L", "K")]

########################
#
#
#######################

def is_known_compound_swedish(word, next_word, known_words, spellchecker, one_letter_words):
    if len(word) < 7: # approx too short for not generating false negatives with compound split
        return False
    for i in range(5, len(word) - 4):
        first = word[:i]
        second = word[i:]
        
        # If one is a three-letter-word, make sure the other one is not too short
        if len(first) < 4 and len(second) < 6:
            continue
        if len(second) < 4 and len(first) < 6:
            continue
            
        if second in known_words:
            if first in known_words or first + 'a' in known_words or first + 'e' in known_words:
                return True
            if first[-1] == 'o' and first[:-1] + 'a' in known_words: #kyrko
                return True
            if first[-1] == 'e' and first[:-1] + 'a' in known_words: #kyrko
                return True
            if first.replace("ium", "ie") in known_words: #sanatorium
                return True
        if first in known_words: # nattåg
            if first[-1] == first[-2] and first[-2] + second in known_words:
                return True
        if second.startswith('s') or second.startswith('-') or second.startswith('e'): #binde
            if first in known_words and second[1:] in known_words:
                return True
    return False
    
def is_known_compound_german(word, next_word, known_words, spellchecker, one_letter_words):
    if len(word) < 7: # approx too short for not generating false negatives with compound split
        return False
    for i in range(4, len(word) - 3):
        first = word[:i]
        second = word[i:]
        if first in known_words and second in known_words:
            return True
        if second.startswith('s') or second.startswith('-'):
            if first in known_words and second[1:] in known_words:
                return True
    return False


def is_known_compound(word, next_word, known_words, spellchecker, one_letter_words):
    if len(word) < 7: # approx too short for not generating false negatives with compound split
        return False
    for i in range(4, len(word) - 3):
        first = word[:i]
        second = word[i:]
        if first in known_words and second in known_words:
            return True
    return False
    
############################
# For suggesting new words
############################


def is_suggestion_frequent_enough(raw_freq, raw_freq_dict, suggested_word):
    if suggested_word in raw_freq_dict and raw_freq_dict[suggested_word] > raw_freq:
        return True
    else:
        """
        if suggested_word not in raw_freq_dict:
            print("suggested_word not in raw_freq_dict[suggested_word]", suggested_word)
        else:
            print("freq for suggestion", raw_freq_dict[suggested_word], suggested_word)
        """
        return False



def get_all_candidates_from_spellchecker(word, next_word, known_words, spellchecker, raw_freq_dict, distance, raw_freq, one_letter_words, is_known_compound_function):
    
    all_canditates_from_spellchecker = []
    
    if any(char.isdigit() for char in word):
        return [] # Don't want to correct things by adding other digits
                
    # E.g. to avoid replace a name
    if word[0].isupper():
        okej_without_upper = False
    else:
        okej_without_upper = True
        
    # Spell checker doesn't seem to handle hyphen and dot well, and long words are very slow
    # distance = 0 means no spell checker
    if distance > 0:
        if "-" not in word and "_" not in word and "." not in word and len(word) < 15:
            candidates = spellchecker.candidates(word)
           
            if candidates:
                if distance == 1:
                    candidates = sorted(candidates) # order doesn't matter here, so to get same output each run
                for candidate in candidates:
                    if is_known(candidate, next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
                        dist = edit_distance(candidate, word)
                        if dist <= distance:
                            if okej_without_upper or candidate[0].isupper():
                                all_canditates_from_spellchecker.append(candidate)
                            
    return all_canditates_from_spellchecker
   
   
def expand_with_one_letter(word, known_words, spellchecker, raw_freq_dict, raw_freq, one_letter_words, is_known_compound_function):

    # Try to expand word with one letter, take the expansion most frequent in corpus
    if len(word) > 3 and "-" not in word:
        expand_suggestion = None
        freq_best_suggestion = 0
        for l in letters:
            suggestion = word + l
            if is_known(suggestion, "", known_words, spellchecker, one_letter_words, is_known_compound_function) and is_suggestion_frequent_enough(raw_freq, raw_freq_dict, suggestion):
                if suggestion in raw_freq_dict and raw_freq_dict[suggestion] > freq_best_suggestion:
                    expand_suggestion = suggestion
                    freq_best_suggestion = raw_freq_dict[suggestion]
            suggestion = l + word
            if is_known(suggestion, "", known_words, spellchecker, one_letter_words, is_known_compound_function) and is_suggestion_frequent_enough(raw_freq, raw_freq_dict, suggestion):
                if suggestion in raw_freq_dict and raw_freq_dict[suggestion] > freq_best_suggestion:
                    expand_suggestion = suggestion
                    freq_best_suggestion = raw_freq_dict[suggestion]
            if expand_suggestion:
                return expand_suggestion
    return None
    
def get_all_expands_with_one_letter(word, known_words, spellchecker, raw_freq_dict, raw_freq, one_letter_words, is_known_compound_function):
    all_expand_suggestions = []
    # Try to expand word with one letter, take the expansion most frequent in corpus
    if len(word) > 3 and "-" not in word:
        for l in letters:
            suggestion = word + l
            if is_known(suggestion, "", known_words, spellchecker, one_letter_words, is_known_compound_function) and is_suggestion_frequent_enough(raw_freq, raw_freq_dict, suggestion):
                all_expand_suggestions.append(suggestion)
                
            suggestion = l + word
            if is_known(suggestion, "", known_words, spellchecker, one_letter_words, is_known_compound_function) and is_suggestion_frequent_enough(raw_freq, raw_freq_dict, suggestion):
                all_expand_suggestions.append(suggestion)
    return all_expand_suggestions
    

def get_new_word(word, next_word, known_words, spellchecker, raw_freq_dict, distance, replacers, one_letter_words, is_known_compound_function, min_freq_in_OCRed_corpus_to_replace):
    new_word_candidates = []

    # To not conflate double-names e.g.
    if len(word)>10 and word[4:-1].count("-") == 2 and not word[4:-1].islower():
        w_p = word.split("-")
        if is_known(w_p[0], next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
            other = get_new_word(w_p[1] + "-" + w_p[2], next_word, known_words, spellchecker, raw_freq_dict, distance, replacers, one_letter_words, is_known_compound_function, min_freq_in_OCRed_corpus_to_replace)
            if other:
                return w_p[0] + "-" + other
        if is_known(w_p[2], next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
            other = get_new_word(w_p[0] + "-" + w_p[1], next_word, known_words, spellchecker, raw_freq_dict, distance, replacers, one_letter_words, is_known_compound_function, min_freq_in_OCRed_corpus_to_replace)
            if other:
                return other + "-" + w_p[2]

    # Always replace "_" and "-" regardless of occurrences
    word = word.replace("_", "").replace("-", "")
    if is_known(word, next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
        return word

    
    if word.isupper() and len(word.replace(".", "")) < 7:
        return None # Too difficult to try to correct
    if len(word) < 4:
        return None # Too many errors with short words
 
    if word[1] == "-": # u-land m.m. frequent error in correction
        return None
        
    if word in raw_freq_dict:
        raw_freq = raw_freq_dict[word]
    elif word.replace("_", "") in raw_freq_dict:
        raw_freq = raw_freq_dict[word.replace("_", "")]
    else:
        raw_freq = 0

  
    for divider in dividers:
        if is_known(word.strip(divider), next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
            if is_suggestion_frequent_enough(raw_freq, raw_freq_dict, word.strip(divider)):
                new_word = word.replace(divider, " " + divider + " ")
                new_word_candidates.append(new_word)
    
    dot_split = word.split(".")
    if len(dot_split) == 2 and dot_split[0].isdigit():
        without_dot = get_new_word(dot_split[1], "", known_words, spellchecker, raw_freq_dict, distance, replacers, one_letter_words, is_known_compound_function, min_freq_in_OCRed_corpus_to_replace)
        if without_dot:
            if is_suggestion_frequent_enough(raw_freq, raw_freq_dict, without_dot):
                new_word_candidates.append(dot_split[0] + " . " + without_dot)
            
            
  
    # Replace with one suggeston at a time
    for replacer in replacers:
        suggestion = word.replace(replacer[0], replacer[1])
        if is_known(suggestion, next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
                if is_suggestion_frequent_enough(raw_freq, raw_freq_dict, suggestion):
                    new_word_candidates.append(suggestion)

    # Try to expand word with one letter, take the expansion most frequent in corpus
    expanded = get_all_expands_with_one_letter(word, known_words, spellchecker, raw_freq_dict, raw_freq, one_letter_words, is_known_compound_function)
    for el in expanded:
        if is_suggestion_frequent_enough(raw_freq, raw_freq_dict, el):
            new_word_candidates.append(el)

        
    # Raw from spell checker
    from_spell_checker = get_all_candidates_from_spellchecker(word, next_word, known_words, spellchecker, raw_freq_dict, distance, raw_freq, one_letter_words, is_known_compound_function)
    for el in from_spell_checker:
        if is_suggestion_frequent_enough(raw_freq, raw_freq_dict, el):
            new_word_candidates.append(el)
        

    if "k-k" in word or "-" in word or "." in word:
        if not (word[-1] == "-" or word[-1] == ".") :
            alpha_word = word.replace("k-k", "ck").replace("-", "").replace(".", "")
            new_word = get_new_word(alpha_word, "-", known_words, spellchecker, raw_freq_dict, distance, replacers, one_letter_words, is_known_compound_function, min_freq_in_OCRed_corpus_to_replace)
            if new_word:
                new_word_candidates.append(new_word)


    if len(new_word_candidates) == 0: # , and with only some hyphens removed
        if "-" in word[:-1]:
            indices_object = re.finditer(pattern='-', string=word)
            indices = [index.start() for index in indices_object]
            for index in indices:
                removed = word[:index] + word[index + 1:]
                if is_known(removed, "-", known_words, spellchecker, one_letter_words, is_known_compound_function):
                    if is_suggestion_frequent_enough(raw_freq, raw_freq_dict, removed):
                        new_word_candidates.append(removed)

    if len(new_word_candidates) == 0: #if still nothing found, try to look at individual parts between hyphens
        if "-" in word:
            parts = word.split("-")
            new_str = []
            all_found = True
            for p in parts:
                if len(p) < 5:
                    all_found = False
                elif is_known(p, "", known_words, spellchecker, one_letter_words, is_known_compound_function):
                    new_str.append(p)
                else:
                    new_w = get_new_word(p, "-", known_words, spellchecker, raw_freq_dict, distance, replacers, one_letter_words, is_known_compound_function, min_freq_in_OCRed_corpus_to_replace)
                    if new_w:
                        new_str.append(new_w)
                    else:
                        all_found = False
            if all_found:
                new_compound = "-".join(new_str)
                if new_compound != word:
                    new_word_candidates.append(new_compound)
                    
    if len(new_word_candidates) == 0:
        # To capture incorrectly tokenized abbreviations
        dot_suggestion = word + "."
        if "-" not in word and "/" not in word and next_word != "-" and is_known(dot_suggestion, next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
                if is_suggestion_frequent_enough(raw_freq, raw_freq_dict, dot_suggestion):
                    new_word_candidates.append(dot_suggestion)
                

    seen = set()
    final_candidates = []
    for el in new_word_candidates:
        if el not in seen:
            identical_without_divider_exists = False
            for d in dividers + ["-"]:
                if d in el:
                    identical_without_divider = el.replace(d, "").replace(" ", "")
                    if identical_without_divider in new_word_candidates:
                        identical_without_divider_exists = True
            if not identical_without_divider_exists:
                final_candidates.append(el)
                seen.add(el)
        
        
    
    if len(final_candidates) == 1:
        if not final_candidates[0].isalpha():
            return final_candidates[0]
        else:
            if is_suggestion_frequent_enough(raw_freq, raw_freq_dict, final_candidates[0]) and raw_freq_dict[final_candidates[0]] >= min_freq_in_OCRed_corpus_to_replace:
                return final_candidates[0]
        
    return None
    
#######################
# For replacing spaced words
#######################
def clean_word(word):
    word = word.replace("z. B.", "").replace("u. a.", "").replace(".", "").replace(",", "").replace("!", "").replace("?", "").replace(":", "").replace("(", "").replace(")", "").replace(";", "").replace("„", "").replace('"', "").replace(":", "").replace("'", "").replace('“', "").replace('‘', "").replace('»', "").replace('«', "").replace('}', "").replace('{', "").replace('*', "").replace("”", "").replace("[", "").replace("]", "").replace("•","").replace("’","").replace("=","").replace(" ", "")
    return word

def more_alone_globbing(sentence, known_words, spellchecker, replacers, space_replaced_dict, one_letter_words, is_known_compound_function):
    simple_tokens = sentence.split(" ")

    to_replace = []
    
    for nr, token in enumerate(simple_tokens):
        if (len(token) == 1 and token.isalpha() and token.islower()) or token == "'s" or "_" in token:
            if nr > 0 and ((simple_tokens[nr - 1].replace("_", "").isalpha() and len(simple_tokens[nr - 1]) > 3) or "_" in simple_tokens[nr - 1])  :
                    new_word_contents = [simple_tokens[nr - 1].replace("_", ""), token]
                    if is_known("".join(new_word_contents), "", known_words, spellchecker, one_letter_words, is_known_compound_function) and not is_known(simple_tokens[nr - 1], "", known_words, spellchecker, one_letter_words, is_known_compound_function):
                        to_replace.append(new_word_contents)
            if nr < len(simple_tokens) - 1 and ((simple_tokens[nr + 1].replace("_", "").isalpha() and len(simple_tokens[nr + 1]) > 3) or "_" in simple_tokens[nr + 1]):
                new_word_contents = [token, simple_tokens[nr + 1].replace("_", "")]
                if is_known("".join(new_word_contents), "", known_words, spellchecker, one_letter_words, is_known_compound_function) and not is_known(simple_tokens[nr + 1], "", known_words, spellchecker, one_letter_words, is_known_compound_function):
                    to_replace.append(new_word_contents)
            # Glob in both directions round token
            if nr < len(simple_tokens) - 1 and ((simple_tokens[nr + 1].replace("_", "").isalpha()) or "_" in simple_tokens[nr + 1]):
                if nr < len(simple_tokens) - 1 and ((simple_tokens[nr + 1].replace("_", "").isalpha()) or "_" in simple_tokens[nr + 1]):
                
                    new_word_contents = [simple_tokens[nr - 1].replace("_", ""), token, simple_tokens[nr + 1].replace("_", "")]
                    if is_known("".join(new_word_contents), "", known_words, spellchecker, one_letter_words, is_known_compound_function) and not is_known(simple_tokens[nr + 1], "", known_words, spellchecker, one_letter_words, is_known_compound_function):
                        to_replace.append(new_word_contents)
    if to_replace:
        for el in to_replace:
            original = " ".join(el)
            new = "_".join(el)
            sentence = sentence.replace(original, new)
            pair = (original, new)
            if pair in space_replaced_dict:
                space_replaced_dict[pair] = space_replaced_dict[pair] + 1
            else:
                space_replaced_dict[pair] = 1
    return sentence

            

def replace_spaced_words(text, known_words, spellchecker, replacers, space_replaced_dict, one_letter_words):
    original_text = copy.copy(text)
    
    # First, search for all spaced words, only keep the longest
    ranges = range(200, 0, -1)
    all_found = [] # To save all candidates
    for nr_of_spaces in ranges:
        re_str = nr_of_spaces * " [^ ][^ ]?"
        # (?: is non-capturing version of regular parentheses
        re_to_use = r"(?: |^|-|\r|\n)([^ ]" + re_str + " [^ ])(?: |$|-|\r|\n)"
        found = re.findall(re_to_use, text)
        
        if len(found) > 0:
            for new_found in found:
                new_found = new_found.strip()
                if new_found == "":
                    continue
                parts = new_found.split()
                add_found = True
                if not clean_word(new_found).replace("-", "").replace("1", "").isalpha():
                    add_found = False
                
                for d in ["=", "•"]:
                    if d in new_found:
                        add_found = False
                
                if new_found.count("-") > 1:
                    add_found = False

                for p in parts:
                    if p in ["dr", "in", "KG"]:
                        add_found = False

                for previously_found in all_found:
                    if new_found in previously_found: # substring of previously found
                        add_found = False
                if add_found:
                    all_found.append(new_found)

    
    all_spaced_split = []
    if len(all_found) > 0:
        for spaced in all_found:
            # An upper case letter in the middle indicates new word, then split it
            spaced_split = []
            last_lower = False
            current_acc = ""
            # Loop through each letter to search for a potential split
            for c in spaced:
                if c == " ":
                    current_acc = current_acc + c
                elif c.isupper() and last_lower and c != "I" and len(current_acc) > 5: #I/l is a frequent OCR misstake
                    spaced_split.append(current_acc.strip())
                    current_acc = ""
                    current_acc = current_acc + c
                    last_lower = c.islower()
                else:
                    current_acc = current_acc + c
                    last_lower = c.islower()
            if len(spaced_split) == 0 or len(current_acc) > 5:
                spaced_split.append(current_acc)
            else:
                spaced_split[-1] = spaced_split[-1] + current_acc # if the last bit is short
                # don't split it
                
            all_spaced_split.extend(spaced_split)
           
    # Make replacements with all known tokens
    # if not known, replace the spaces with underscore
    all_replaced = []
    all_spaced_split_sorted = sorted(all_spaced_split, key=len, reverse=True)
       
    #not_found_spaced = False
    for spaced in all_spaced_split_sorted:
        
        replace_with_hyphens = " " + spaced.replace(" ", "_") + " "
        
             
        all_replaced.append((spaced, replace_with_hyphens))
        text = text.replace(spaced, replace_with_hyphens)
    
   
    
    # Gather statics
    for pair in all_replaced:
        if pair in space_replaced_dict:
            space_replaced_dict[pair] = space_replaced_dict[pair] + 1
        else:
            space_replaced_dict[pair] = 1
  
    return text, all_replaced


###########
# Search for unknown words
############

def is_hyphen_likely_word(word):
    sub_words = word.split("-")
    if len(sub_words) < 1:
        return False
    for el in sub_words:
        if el == "":
            return False
            
    all_starters = "".join([w[0] for w in sub_words])
    if all_starters.isupper() and not(sub_words[1].isupper()):
        return True
        
    for sub_word in sub_words:
        if sub_word.isnumeric():
            return True
            
    if sub_words[0].isupper() and sub_words[1].islower():
        return True
    
    return False
    
def is_known(word, next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
    #spell_checker_output = spellchecker.unknown([word])
    #len(spell_checker_output) == 0 or
    if not next_word.strip() == "." and len(word) == 1 and word.isalpha() and word not in one_letter_words:
        if next_word != ".": # likely abbreviation
            return False
        else:
            print(word, next_word)
    
    for nr in [1, 2, 3, 4]:
        if word in [el*nr for el in dividers]: # If it's only dividers in a word, consider it correct
            return True
    
    # Compounds with numbers
    string_without_digits = ''.join([i for i in word if not i.isdigit()])
    if word != string_without_digits and string_without_digits.isalpha() and len(word) - len(string_without_digits) > 1:
        if len(string_without_digits) > 6 and is_known(string_without_digits, next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
            return True
        
    if word.replace("-", "").replace("=", "").replace("_", "").replace("•", "").replace("—", "").replace(".", "").strip() == "":
        return True
        
    word = word.strip()
    orig_word = word
    word = word.lower()
    if word in known_words or orig_word in known_words:
        return True
    if word.rstrip(".") in known_words or orig_word.rstrip(".") in known_words:
        return True
        
    if word.replace("-", "").replace("—", "").replace(".", "").replace(",", "").replace("°", "").replace(":", "").replace("Nr.", "").replace("g", "").replace("/", "").replace("'", "").isdigit():
        return True
    if "/" in word:
        parts = word.split("/")
        missing_subword = False
        for part in parts:
            if not is_known(part, next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
                missing_subword = True
        if not missing_subword:
            return True
            
    if is_known_compound_function(word, next_word, known_words, spellchecker, one_letter_words):
    #if is_known_compound(word, next_word, known_words, spellchecker, one_letter_words):
        return True
    
    if "-" in orig_word:
        #if is_known(word.replace("-", ""), next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
        #    return True
            
        if is_hyphen_likely_word(orig_word):
            return True
            
        all_subwords_known = True
        sub_words = word.split("-")
        
        for sub_word in sub_words:
            if len(sub_word) == 0:
                all_subwords_known = False
            elif len(sub_word) < 6: # Subwords need to be long enough
                all_subwords_known = False
            elif not is_known(sub_word, next_word, known_words, spellchecker, one_letter_words, is_known_compound_function):
                all_subwords_known = False
        if all_subwords_known:
            return True
 
    return False
    
    
#####################
# Main function for searching words not in terminologies
####################

def search_not_found(text, known_words, not_found_dict, not_found_dict_corrected, corrected_dict, space_replaced_dict, spellchecker, raw_freq_dict, distance, replacers, one_letter_words, is_known_compound_function, min_freq_in_OCRed_corpus_to_replace, not_to_correct):
    text = text.replace("\r", "\n").replace("  ", " ")
    sentences = text.split("\n")
    
    not_found_for_text_dict = {}
    not_found_for_text_after_corrected_dict = {}
    nr_of_words = 0
    new_text = [] # to add tokens in a new created text
    
    for sentence in sentences:
        
        updated_sentence = []
        sentence, all_replaced = replace_spaced_words(sentence, known_words, spellchecker, replacers, space_replaced_dict, one_letter_words)
        
        sentence = sentence.strip()
        sentence = sentence.replace("  ", " ")
        
        sentence = more_alone_globbing(sentence, known_words, spellchecker, replacers, space_replaced_dict, one_letter_words, is_known_compound_function)
        changed_at_least_one = False
        
        tokens = word_tokenize(sentence)
        for word_nr, word in enumerate(tokens):
            if word_nr >= len(tokens) - 1:
                next_word = ""
            else:
                next_word = tokens[word_nr + 1]
            to_print = False
            if (len(word) == 1 or word[0] == "-") and word not in dividers and word not in ["&", "—", "%", "-", "’"] and not word.isdigit():

                to_print = True
            if word not in dividers: # Don't include dividers in the statics
                nr_of_words = nr_of_words + 1
                
            if not is_known(word, next_word, known_words, spellchecker, one_letter_words, is_known_compound_function) and not word in not_to_correct:
                #if to_print:
                #    print("Not known\n")
                # Add statics of word not found
                if word not in not_found_for_text_dict:
                    not_found_for_text_dict[word] = 1
                else:
                    not_found_for_text_dict[word] = not_found_for_text_dict[word] + 1
                    
                if word not in not_found_dict:
                    not_found_dict[word] = 1
                else:
                    not_found_dict[word] = not_found_dict[word] + 1
                   
                # Try to find a new word
                new_word = get_new_word(word, next_word, known_words, spellchecker, raw_freq_dict, distance, replacers, one_letter_words, is_known_compound_function, min_freq_in_OCRed_corpus_to_replace)
          
                if new_word: # An alterantive word found
                    updated_sentence.append(new_word)
                    changed_at_least_one = True
                    
                    if (word, new_word) in corrected_dict:
                        corrected_dict[(word, new_word)] = corrected_dict[(word, new_word)] + 1
                    else:
                        corrected_dict[(word, new_word)] = 1
                else: # use the original, because no alternative word was found
                    updated_sentence.append(word)
                    
                    # Then add statics for no correction being found
                    
                    if word not in not_found_for_text_after_corrected_dict:
                        not_found_for_text_after_corrected_dict[word] = 1
                    else:
                        not_found_for_text_after_corrected_dict[word] = not_found_for_text_after_corrected_dict[word] + 1
                        
                    
                    if word not in not_found_dict_corrected:
                        not_found_dict_corrected[word] = 1
                    else:
                        not_found_dict_corrected[word] = not_found_dict_corrected[word] + 1
                    
            else: # Word is known, then just add it as-is to the updated sentence
                
                updated_sentence.append(word.replace("_", ""))
                
        if changed_at_least_one:
            new_text.append(TreebankWordDetokenizer().detokenize(updated_sentence))
            #new_text.append(" ".join(updated_sentence))
        else:
            new_text.append(sentence)
       
    new_text_str =  "\n".join(new_text)

    if nr_of_words == 0:
        return None, None, 1, 1, 0, ""
        
    nr_of_not_found = sum(not_found_for_text_dict.values())
    error_proportion = nr_of_not_found/nr_of_words
    nr_of_not_found_corrected = sum(not_found_for_text_after_corrected_dict.values())
    error_proportion_after_corrected = nr_of_not_found_corrected/nr_of_words
    return not_found_for_text_dict, not_found_for_text_after_corrected_dict, error_proportion, error_proportion_after_corrected, nr_of_words, new_text_str

###########
# Build the word lists
############

def get_words(file_name, to_exclude_from_terminology):
    words = []
    with open(file_name) as f:
        for line in f:
            line = line.strip()
            if line not in to_exclude_from_terminology:
                words.append(line)
                words.append(line.lower())
    return words
    
def get_known_words(terminologies_file_name, to_exclude_from_terminology):
    known_words = []
    with open(terminologies_file_name) as terminology_file:
        file_names = terminology_file.readlines()
        print("Nr of word lists found: " + str(len(file_names)))
        for file_name in file_names:
            file_name = file_name.strip()
            if not os.path.exists(file_name):
                print("The file " + file_name + " does not exist (given as a file in " + terminologies_file_name + ")")
                exit()
            else:
                known_words.extend(get_words(file_name, to_exclude_from_terminology))

    known_words = set(known_words)
    print("Nr of words in word lists: ", len(known_words))
    return known_words
        
    
##############
# Main function below + small help function to that method (compare_folder)
###############

def get_year_number(file_path):
    year, number = os.path.basename(file_path).split("_vol")
    nr_year = "".join([c for c in year if c.isdigit()])
    nr_number = "".join([c for c in number if c.isdigit()])
    year_number = float(nr_year + "." + nr_number)
    return str(year_number)

#Not used currently
def get_confidence_interval(proportion, nr_of_observed):
    print("proportion", nr_of_observed)
    print("nr_of_observed", nr_of_observed)
    if nr_of_observed == 0:
        return (0,0)
        
    intervall = 1.96 * math.sqrt(proportion*(1-proportion)/nr_of_observed)
    min = proportion - intervall
    max = proportion + intervall
    if min < 0:
        min = 0
    if max > 1:
        max = 1
    return (min, max)
    
def plot_output(file_names, error_props, all_nr_of_words, colors, output_folder, output_filename, okay_error_proportion):

    plt.bar(file_names, error_props, color=colors)
        
    plt.ylim(-0.05, 0.5)
    plt.xticks([], [])
    
    next_allowed_to_annotate = len(file_names)*0.005
    last_annotated = -next_allowed_to_annotate
    
    for nr, (file_name, error_prop, color) in enumerate(zip(file_names, error_props, colors)):
        if color == "maroon" and error_prop > okay_error_proportion:
            if nr > last_annotated + next_allowed_to_annotate:
                plt.text(nr, error_prop, file_name, fontsize="0.01", rotation=90, color="grey")
                last_annotated = nr
        
        
    plt.title(output_filename)
    plt.ylabel("Word error proportion")
    plt.xlabel("Issue")
    pdf_output = os.path.join(output_folder, output_filename + ".pdf")
    plt.savefig(pdf_output, format='pdf')
    plt.clf()

# Help function for error writing statistics to file
def write_error_propotion_to_file(write_to, error_props, file_names, all_nr_of_words, okay_error_proportion):
    write_to.write("\n Error proportion more than 0.5\n")
    write_to.write("==================================\n")
    write_to.write("\t".join(["Proportion", "File name", "Nr of words"]) + "\n")
    error_tuples = [(score, name, nr_of_words) for (score, name, nr_of_words) in zip(error_props, file_names, all_nr_of_words)]
    
    file_scores = sorted(error_tuples, reverse=True)
    for (score, name, nr_of_words) in file_scores:
        if score > okay_error_proportion:
            write_to.write(str(round(score,2)) + "\t" + name + "\t" + str(nr_of_words) + "\n")
        if score < 0:
            write_to.write("EMPTY" + "\t" + name + "\n")

# Help function for error frequency statistics to file
def write_frequencty_of_not_found(write_to, not_found_dict):
    not_found_list = sorted([(nr, word) for (word, nr) in not_found_dict.items() if nr > 1], reverse=True)
    write_to.write("\t".join(["\nNr of unique not found: ", str(len(not_found_dict.keys())), "\n"]))
    write_to.write("Not found freq > 1" +  "\n")
    write_to.write("==================================\n")
    previous_not_found_nr = math.inf
    for nr, word in not_found_list:
        if nr < previous_not_found_nr:
            write_to.write("\n" + str(nr) + "\n")
            previous_not_found_nr = nr
        write_to.write(word + "\n")
 
def get_raw_frequency(folder):
    print("Getting frequencies")
    raw_freq_dict = {}
    
    files = sorted(glob.glob(os.path.join(folder, "*.txt")))
    for f in files:
        with open(f, encoding='utf-8-sig') as opened:
            content = opened.read()
            content = content.replace("\r", "\n")
            paragraphs = content.split("\n")
            for para in paragraphs:
                for word in word_tokenize(para):
                    if word not in raw_freq_dict:
                        raw_freq_dict[word] = 1
                    else:
                        raw_freq_dict[word] = raw_freq_dict[word] + 1
    return raw_freq_dict

def combine_dictionaries_in_list(raw_freq_dict_list):
    combined_dict = {}
    
    for el in raw_freq_dict_list:
        for word, freq in el.items():
            if word in combined_dict:
                combined_dict[word] = combined_dict[word] + freq
            else:
                combined_dict[word] = freq
    return combined_dict
    
###########################################
# This is the main external function to run
###########################################



def compare_folder(corpus_folder, terminologies_file_name, output_filename, main_output,  main_output_text, periodical, language, distance=1, replacers=default_replacers, one_letter_words = ["m", "g", "a"], freq_dict_window=10, okay_error_proportion=0.05, only_create_folders=False, is_known_compound_function=is_known_compound, to_exclude_from_terminology = [], min_freq_in_OCRed_corpus_to_replace=2, not_to_correct=[]):


    # Read terminologies
    if not os.path.exists(terminologies_file_name):
        print("The file " + terminologies_file_name + " does not exist")
        exit()
    known_words = get_known_words(terminologies_file_name, to_exclude_from_terminology)

    # Initialize spellChecker
    try:
        spellchecker = SpellChecker(language=language, distance=distance)
    except ValueError:
        print("There is no built-in spelling correction for the language " + language + ". The spelling correction will rely entirely on the word lists you provide.")
        spellchecker = SpellChecker(local_dictionary = "", distance=distance)
        
    spellchecker.word_frequency.load_words(list(known_words))

    # Create folders to store statistcs output
    if not os.path.exists(main_output):
        os.mkdir(main_output)
    output_folder = os.path.join(main_output, periodical)
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)
        print("Creating: ", output_folder)
    else:
        print("Use existing folder: ", output_folder)
        
        
    # Create folders to store text output
    if not os.path.exists(main_output_text):
        os.mkdir(main_output_text)
    output_folder_text = os.path.join(main_output_text, periodical)
    if not os.path.exists(output_folder_text):
        os.mkdir(output_folder_text)
        print("Creating: ", output_folder_text)
    else:
        print("Use existing folder: ", output_folder_text)
    

    if only_create_folders:
        return
        
    file_names = []
    error_props = []
    error_props_corrected = []
    colors = []
    colors_corrected = []
    all_nr_of_words = []
    not_found_dict = {}
    not_found_dict_corrected = {}
    corrected_dict = {}
    space_replaced_dict = {}
    
    write_to = open(os.path.join(output_folder, output_filename), "w")
    output_filename_corrected = "corrected_" + output_filename
    output_filename_replacements = "replacements_made_" + output_filename
    output_filename_space_replaced = "space_replaced_" + output_filename
    output_filename_not_found = "not_found_" + output_filename
        
    write_to_corrected = open(os.path.join(output_folder, output_filename_corrected), "w")
    write_to_replacements = open(os.path.join(output_folder, output_filename_replacements), "w")
    write_to_space_replaced = open(os.path.join(output_folder, output_filename_space_replaced), "w")
    write_to_not_found = open(os.path.join(output_folder, output_filename_not_found), "w")
    
    
    folders = sorted(glob.glob(os.path.join(corpus_folder, "*")))
    if not os.path.exists(corpus_folder):
        print("The folder ", corpus_folder, "does not exist. Exiting")
        exit()
    if len(folders) == 0:
        print("no subfolders found in ", corpus_folder, ". Exiting")
        exit()
    else:
        print(str(len(folders)) +  " nr of subfolders found in ", corpus_folder)
        
    # First read through all files ones, to just gather frequency statistics for
    # unprocessed files
    raw_freq_dict_list = []
    for folder in folders:
        raw_freq_dict_for_folder = get_raw_frequency(folder)
        raw_freq_dict_list.append(raw_freq_dict_for_folder)
    
    
    freq_dict_window = 5 # = the total numer of folders is the current + 2*FREQ_DIC_WINDOW
    for nr, folder in enumerate(folders):
    
        print(folder)
        
        start_freq_folder = nr - freq_dict_window
        end_freq_folder = nr + freq_dict_window + 1
        
        if start_freq_folder < 0:
            start_freq_folder = 0
            end_freq_folder = start_freq_folder + 2*freq_dict_window + 1
        if end_freq_folder > len(raw_freq_dict_list):
            end_freq_folder = len(raw_freq_dict_list)
            start_freq_folder = end_freq_folder - (2*freq_dict_window + 1)
            if start_freq_folder < 0:
                start_freq_folder = 0
            
        
        part_of_freq_dict_list = raw_freq_dict_list[start_freq_folder:end_freq_folder]
            
        raw_freq_dict = combine_dictionaries_in_list(raw_freq_dict_list)

        basefolder_name = os.path.basename(folder)
        
        # Folder for text output
        output_text_sub_folder = os.path.join(output_folder_text, basefolder_name)
        if not os.path.exists(output_text_sub_folder):
            os.mkdir(output_text_sub_folder)

        files = sorted(glob.glob(os.path.join(folder, "*.txt")))
        for f in files:
            file_base_name = os.path.basename(f)
            file_names.append(file_base_name)
            
            output_for_text_file_name = os.path.join(output_text_sub_folder, file_base_name)
            output_for_text_file = open(output_for_text_file_name, "w")
                      
            write_to.write("\n------" + file_base_name + "------\n")
            write_to_corrected.write("\n------" + file_base_name + "------\n")
            with open(f, encoding='utf-8-sig') as opened:
                content = opened.read()
                 
                not_found_for_text_dict, not_found_for_text_after_corrected_dict, error_proportion, error_proportion_after_corrected, nr_of_words, new_text_str = search_not_found(content, known_words, not_found_dict, not_found_dict_corrected, corrected_dict, space_replaced_dict, spellchecker, raw_freq_dict, distance, replacers, one_letter_words, is_known_compound_function, min_freq_in_OCRed_corpus_to_replace, not_to_correct)

                all_nr_of_words.append(nr_of_words)
                if not_found_for_text_dict == None:
                    write_to.write("SEEMS EMPTY\n")
                    write_to_corrected.write("SEEMS EMPTY\n")
                    error_props.append(-0.05)
                    error_props_corrected.append(-0.05)
                    colors.append("black")
                    colors_corrected.append("black")
                else:
                    write_to.write("\t".join(["Error proportion: ", str(error_proportion), "\n"]))
                    write_to.write("\t".join(["Nr of words: ", str(nr_of_words), "\n"]))
                    
                    write_to_corrected.write("\t".join(["Error proportion: ", str(error_proportion_after_corrected), "\n"]))
                    write_to_corrected.write("\t".join(["Nr of words: ", str(nr_of_words), "\n"]))
                    
                    sorted_not_found = sorted([(nr, word) for (word, nr) in not_found_for_text_dict.items()], reverse=True)
                    for (nr, word) in sorted_not_found:
                        write_to.write(word + "\t" + str(nr) + "\n")

                    sorted_not_found_corrected = sorted([(nr, word) for (word, nr) in not_found_for_text_after_corrected_dict.items()], reverse=True)
                    for (nr, word) in sorted_not_found_corrected:
                        write_to_corrected.write(word + "\t" + str(nr) + "\n")
                      
                    
                    error_props.append(error_proportion)
                    error_props_corrected.append(error_proportion_after_corrected)
                    
                    if error_proportion <= okay_error_proportion:
                        colors.append("green")
                    else:
                        if nr_of_words > 100:
                            colors.append("maroon")
                        else:
                            colors.append("black")
                            
                    if error_proportion_after_corrected <= okay_error_proportion:
                        colors_corrected.append("green")
                    else:
                        if nr_of_words > 100:
                            colors_corrected.append("maroon")
                        else:
                            colors_corrected.append("black")
                            
                output_for_text_file.write(new_text_str)
            output_for_text_file.close()
            

    assert(len(error_props) == len(file_names))
    assert(len(error_props_corrected) == len(file_names))
    
    # Write frequency of not found
    write_frequencty_of_not_found(write_to, not_found_dict)
    
    # Write not found after corrected to separate file
    write_frequencty_of_not_found(write_to_not_found, not_found_dict_corrected)
        
    # Write error proportion
    write_error_propotion_to_file(write_to, error_props, file_names, all_nr_of_words, okay_error_proportion)
    write_error_propotion_to_file(write_to_corrected, error_props_corrected, file_names, all_nr_of_words, okay_error_proportion)
            
    # Write corrected errors
    last_nr_of_replaced = math.inf
    corrected_list = sorted([(nr, word) for (word, nr) in corrected_dict.items()], reverse=True)
    write_to_replacements.write("\nReplacements made\n")
    write_to_replacements.write("==================================\n")
    for (nr, word) in corrected_list:
        if nr < last_nr_of_replaced:
            write_to_replacements.write("\n" + str(nr) + "\n")
            write_to_replacements.write("-----\n")
            last_nr_of_replaced = nr
    
        old, replaced = word
        write_to_replacements.write(old + "\t" + replaced + "\n")
        
    # Write space replaced words
    last_nr_of_replaced_space = math.inf
    space_replaced_list = sorted([(nr, word) for (word, nr) in space_replaced_dict.items()], reverse=True)
    write_to_space_replaced.write("\nSpace replaced\n")
    write_to_space_replaced.write("==================================\n")
    for (nr, word) in space_replaced_list:
        if nr < last_nr_of_replaced_space:
            write_to_space_replaced.write("\n" + str(nr) + "\n")
            write_to_space_replaced.write("-----\n")
            last_nr_of_replaced_space = nr
        old, replaced = word
        write_to_space_replaced.write(old + "\t" + replaced + "\n")
     
    write_to.close()
    write_to_corrected.close()
    write_to_replacements.close()
    write_to_space_replaced.close()
    write_to_not_found.close()

    # Plot error
    plot_output(file_names, error_props, all_nr_of_words, colors, output_folder, output_filename, okay_error_proportion)
    plot_output(file_names, error_props_corrected, all_nr_of_words, colors, output_folder, output_filename_corrected, okay_error_proportion)
