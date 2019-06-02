import argparse
import praw 
import prawcore.exceptions
from psaw import PushshiftAPI
import sys
import json
import numpy as np
from feature_extraction.Annotation import Tweet
from feature_extraction.Annotation import TwitterDataset
from feature_extraction.Features import FeatureExtractor
from feature_extraction.word_embeddings import load_saved_word_embeddings
from models.hmm_veracity import HMM

from sklearn.linear_model import LogisticRegression

from joblib import dump, load

import reddit_fetcher
import data_loader

def main(argv):

    data = [json.loads(line.strip()) for line in open('twitter_threads/threads.json').readlines()]
    threads = {}

    features = {
        'text': True,
        'lexicon' : False,
        'sentiment' : True,
        'reddit' : False,
        'most_freq' : False,
        'bow' : False,
        'pos' : False,
        'wembs' : True 
    }

    num_to_stance = {
        0 : 'Supporting',
        1 : 'Denying',
        2 : 'Querying',
        3 : 'Commenting'
    }

    load_saved_word_embeddings(300, False)
    clf = load('./models/svm_t_s_w2v.joblib')

    classification = {'true':0, 'false':0}

    for thread in data:

        if len(thread['children']) < 2:
            continue


        root_id = thread['root']['id']
        threads = [Tweet(t) for t in thread['children']]

        # dataset = TwitterDataset()
        # dataset.add_submission_branch(thread['children'])

        extractor = FeatureExtractor('test', test=True)
        vectors = extractor.create_feature_vectors(threads, features['text'], features['lexicon'], features['sentiment'], features['reddit'], features['most_freq'], features['bow'], features['pos'], features['wembs'], True) # is live, to avoid annotations

        flattened_vectors = []
        for vec in vectors:
            flat_vec = []
            for group in vec:
                if type(group) == list:
                    flat_vec.extend(group)
                else:
                    flat_vec.append(group)
            flattened_vectors.append(flat_vec)

        stance_predicts = clf.predict(flattened_vectors)
        # print(stance_predicts)

        hmm_clf = load('./models/hmm_1_branch.joblib') 
        rumour_veracity = hmm_clf.predict([stance_predicts])[0]

        is_true = None
        if rumour_veracity:
            is_true = 'true'
        else:
            is_true = 'false'
        
        classification[is_true] += 1

        # if is_true:
        #     print("Crowd stance ordered by comment time:\n")
        #     print([num_to_stance[x] for x in stance_predicts])
        #     print(thread['root']['text'])
        #     break

        # print("It seems the crowds stance thinks submission '{}' is {}".format(thread['root']['text'], is_true))

        # break
    print(classification)

   
if __name__ == "__main__":
    main(sys.argv[1:])