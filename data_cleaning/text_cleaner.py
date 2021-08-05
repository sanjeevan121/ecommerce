import pandas as pd
#from dask.distributed import Client, progress
import json
import numpy as np
import multiprocessing as mp
#import dask.dataframe as dd
import nltk
import re
from nltk import word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from nltk.stem import WordNetLemmatizer
from autocorrect import Speller

class cleaner:
    def __init__(self,json_file=None,csv_file=None,contradictions_file='data_cleaning/contradictions.json'):
        if csv_file!=None:
            self.df = pd.read_csv(csv_file,engine='python')
        if json_file!=None:
            self.df=pd.read_json(json_file,lines=True)
        if contradictions_file!=None:
            self.contractions_dict=json.loads(open(contradictions_file).read())

    def remove_blank_spaces(self):
        self.df = self.df.replace(r'^\s*$', np.nan, regex=True)
        self.df['reviewText'] = self.df['reviewText'].fillna(value='no review', inplace=True)
        self.df['reviewText'] = self.df['reviewText'].apply(lambda x: x.replace('\n', ''))
        return self.df

    def remove_bad_columns(self):
        self.df = self.df.drop(columns=['reviewTime','image'], axis=1, inplace=True)

        return self.df
    def to_lower(self,text):
        """
        Converting text to lower case as in, converting "Hello" to "hello" or "HELLO" to "hello".
        """

        text=' '.join([w.lower() for w in word_tokenize(text)])
        return text
    def expand_contractions(self,text):
        """
        Expanding contractions to base english words as in ,converting 'y'all' to you all
        """

        contractions_pattern = re.compile('({})'.format('|'.join(self.contractions_dict.keys())),
                                          flags=re.IGNORECASE | re.DOTALL)

        def expand_match(contraction):
            match = contraction.group(0)
            first_char = match[0]
            expanded_contraction = self.contractions_dict.get(match) \
                if self.contractions_dict.get(match) \
                else self.contractions_dict.get(match.lower())
            expanded_contraction = expanded_contraction
            return expanded_contraction

        expanded_text = contractions_pattern.sub(expand_match, text)
        expanded_text = re.sub("'", "", expanded_text)
        return expanded_text

    def remove_Tags(self,text):
        """
        take string input and clean string without tags.
        use regex to remove the html tags.
        """
        cleaned_text = re.sub('<[^<]+?>', '', text)
        return cleaned_text

    def escape_ansi(self,text):
        ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
        text= ansi_escape.sub('', text)
        return text

    def remove_punct(self,text):
        """
        take string input and clean string without punctuations.
        use regex to remove the punctuations.
        """
        text=''.join(c for c in text if c not in punctuation)
        return text
    def lemmatize(self,text):
        """
        take string input and lemmatize the words.
        use WordNetLemmatizer to lemmatize the words.
        """
        stopword = stopwords.words('english')
        wordnet_lemmatizer = WordNetLemmatizer()
        word_tokens = nltk.word_tokenize(text)
        lemmatized_word = [wordnet_lemmatizer.lemmatize(word) for word in word_tokens]
        text= (" ".join(lemmatized_word))
        return text

    def remove_stopwords(self,text):
        """
        removes all the stop words like "is,the,a, etc."
        5 lines of code can be written in one line as:
            return ' '.join([w for w in word_tokenize(sentence) if not w in stop_words])
        """
        stop_words = set(stopwords.words('english'))
        clean_sent = []
        for w in word_tokenize(text):
            if not w in stop_words:
                clean_sent.append(w)
        text= " ".join(clean_sent)
        return text
    def autospell(self,text):
        """
        correct the spelling of the word.
        """
        speller = Speller('en')
        spells = [speller(w) for w in (nltk.word_tokenize(text))]
        text= " ".join(spells)
        return text

    def preprocess(self,text):
        text = self.expand_contractions(text)
        text = self.to_lower(text)
        text = self.remove_Tags(text)
        text = self.escape_ansi(text)
        text = self.remove_punct(text)
      #  text = self.remove_stopwords(text)
        text = self.autospell(text)
        text = self.lemmatize(text)
        return text
if __name__=="__main__":
    cleaner=cleaner()