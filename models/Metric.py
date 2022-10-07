from transformers import BertTokenizer
import numpy as np
import json
id2sentiment = {0: 'none', 1: 'positive', 2: 'negative', 3:'neutral'}


class Metric():
    def __init__(self, args, all_gold_aspect, all_gold_aspect_sentiment, all_gold_opinion, all_pred_aspect,
                 all_pred_aspect_sentiment, all_pred_aspect_sentiment_logit, all_pred_opinion,
                 all_pred_opinion_sentiment_logit, all_gold_mask, gold_instances):
        self.args = args
        self.gold_aspect = all_gold_aspect
        self.gold_aspect_sentiment = all_gold_aspect_sentiment
        self.gold_opinion = all_gold_opinion

        self.pred_aspect = all_pred_aspect
        self.pred_aspect_sentiment = all_pred_aspect_sentiment
        self.pred_aspect_sentiment_logit = all_pred_aspect_sentiment_logit

        self.pred_opinion = all_pred_opinion
        self.pred_opinion_sentiment_logit = all_pred_opinion_sentiment_logit

        self.gold_mask = all_gold_mask
        self.gold_instances = gold_instances
        self.tokenizer = BertTokenizer.from_pretrained(args.init_vocab, do_lower_case=args.do_lower_case)

    def P_R_F1(self, gold_num, pred_num, correct_num):
        precision = correct_num / pred_num if pred_num > 0 else 0
        recall = correct_num / gold_num if gold_num > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        return (precision, recall, f1)

    def num_4_eval(self, gold, pred, gold_num, pred_num, correct_num):
        correct = set(gold) & set(pred)
        gold_num += len(set(gold))
        pred_num += len(set(pred))
        correct_num += len(correct)
        return gold_num, pred_num, correct_num

    def score_triples(self):
        correct_aspect_num,correct_opinion_num,correct_apce_num,correct_pairs_num,correct_num = 0,0,0,0,0
        gold_aspect_num,gold_opinion_num,gold_apce_num,gold_pairs_num,gold_num = 0,0,0,0,0
        pred_aspect_num,pred_opinion_num,pred_apce_num,pred_pairs_num,pred_num = 0,0,0,0,0

        # gold_aspect_num_length1, gold_aspect_num_length2, gold_aspect_num_length3, gold_aspect_num_length4, gold_aspect_num_length5 = 0,0,0,0,0
        # pred_aspect_num_length1, pred_aspect_num_length2, pred_aspect_num_length3, pred_aspect_num_length4, pred_aspect_num_length5 = 0,0,0,0,0
        # correct_aspect_num_length1, correct_aspect_num_length2, correct_aspect_num_length3, correct_aspect_num_length4, correct_aspect_num_length5 =  0,0,0,0,0
        #
        # gold_opinion_num_length1, gold_opinion_num_length2, gold_opinion_num_length3, gold_opinion_num_length4, gold_opinion_num_length5 = 0,0,0,0,0
        # pred_opinion_num_length1, pred_opinion_num_length2, pred_opinion_num_length3, pred_opinion_num_length4, pred_opinion_num_length5 = 0,0,0,0,0
        # correct_opinion_num_length1, correct_opinion_num_length2, correct_opinion_num_length3, correct_opinion_num_length4, correct_opinion_num_length5 =  0,0,0,0,0

        if self.args.output_path:
            result = []
            aspect_text,opinion_text = [],[]
        for i in range(len(self.gold_instances)):
            '''实体长度实验'''
            # gold_aspect_length1, gold_aspect_length2, gold_aspect_length3, gold_aspect_length4, gold_aspect_length5 = [], [], [], [], []
            # pred_aspect_length1, pred_aspect_length2, pred_aspect_length3, pred_aspect_length4, pred_aspect_length5 = [], [], [], [], []
            #
            # gold_opinion_length1, gold_opinion_length2, gold_opinion_length3, gold_opinion_length4, gold_opinion_length5 = [], [], [], [], []
            # pred_opinion_length1, pred_opinion_length2, pred_opinion_length3, pred_opinion_length4, pred_opinion_length5 = [], [], [], [], []


            bert_tokens = []
            spans = self.gold_instances[i]['spans']
            start2idx = []
            end2idx = []
            bert_tokens.append(self.tokenizer.cls_token)
            for token in self.gold_instances[i]['tokens']:
                start2idx.append(len(bert_tokens))
                sub_tokens = self.tokenizer.tokenize(token)
                bert_tokens += sub_tokens
                end2idx.append(len(bert_tokens) - 1)
            bert_tokens.append(self.tokenizer.sep_token)
            bert_spans = [[start2idx[span[0]], end2idx[span[1]], span[2]] for span in spans]
            gold_aspect,gold_opinion,gold_apce,gold_pairs,gold_triples = self.find_gold_triples(i, bert_spans, bert_tokens)
            # assert len(gold_triples) == len(self.gold_instances[i]['triples'])
            pred_aspect,pred_opinion,pred_apce,pred_pairs,pred_triples = self.find_pred_triples(i, bert_spans, bert_tokens)

            if self.args.output_path:
                result.append({"sentence": self.gold_instances[i]['sentence'],
                                     "triple_list_gold": [gold_triple for gold_triple in set(gold_triples)],
                                     "triple_list_pred": [pred_triple for pred_triple in set(pred_triples)],
                                    "new": [new_triple for new_triple in (set(pred_triples) - set(gold_triples))],
                                    "lack": [lack_triple for lack_triple in (set(gold_triples) - set(pred_triples))]
                                     })
                aspect_text.append({"sentence": self.gold_instances[i]['sentence'],
                                    'gold aspect': [gold_as for gold_as in set(gold_aspect)],
                                    'pred aspect': [pred_as for pred_as in set(pred_aspect)],
                                    "new": [new_as for new_as in (set(pred_aspect) - set(gold_aspect))],
                                    "lack": [lack_as for lack_as in (set(gold_aspect) - set(pred_aspect))]})
                opinion_text.append({"sentence": self.gold_instances[i]['sentence'],
                                    'gold aspect': [gold_op for gold_op in set(gold_opinion)],
                                    'pred aspect': [pred_op for pred_op in set(pred_opinion)],
                                    "new": [new_op for new_op in (set(pred_opinion) - set(gold_opinion))],
                                    "lack": [lack_op for lack_op in (set(gold_opinion) - set(pred_opinion))]})


            gold_aspect_num, pred_aspect_num, correct_aspect_num = self.num_4_eval(gold_aspect, pred_aspect,
                                                                                   gold_aspect_num,
                                                                                   pred_aspect_num, correct_aspect_num)

            gold_opinion_num, pred_opinion_num, correct_opinion_num = self.num_4_eval(gold_opinion, pred_opinion,
                                                                                   gold_opinion_num,
                                                                                   pred_opinion_num, correct_opinion_num)

            gold_apce_num, pred_apce_num, correct_apce_num = self.num_4_eval(gold_apce, pred_apce, gold_apce_num,
                                                                             pred_apce_num, correct_apce_num)

            gold_apce_num, pred_apce_num, correct_apce_num = self.num_4_eval(gold_apce, pred_apce, gold_apce_num,
                                                                             pred_apce_num, correct_apce_num)

            gold_pairs_num, pred_pairs_num, correct_pairs_num = self.num_4_eval(gold_pairs, pred_pairs, gold_pairs_num,
                                                                             pred_pairs_num, correct_pairs_num)

            gold_num, pred_num, correct_num = self.num_4_eval(gold_triples, pred_triples, gold_num,
                                                                                pred_num, correct_num)

        #     for aspect_G in gold_aspect:
        #         aspect_length = aspect_G.split(' ')
        #         if len(aspect_length) == 1:
        #             gold_aspect_length1.append(aspect_G)
        #         elif len(aspect_length) == 2:
        #             gold_aspect_length2.append(aspect_G)
        #         elif len(aspect_length) >= 3:
        #             gold_aspect_length3.append(aspect_G)
        #         elif len(aspect_length) == 4:
        #             gold_aspect_length4.append(aspect_G)
        #         elif len(aspect_length) >= 5:
        #             gold_aspect_length5.append(aspect_G)
        #
        #     for aspect_P in pred_aspect:
        #         aspect_length = aspect_P.split(' ')
        #         if len(aspect_length) == 1:
        #             pred_aspect_length1.append(aspect_P)
        #         elif len(aspect_length) == 2:
        #             pred_aspect_length2.append(aspect_P)
        #         elif len(aspect_length) >= 3:
        #             pred_aspect_length3.append(aspect_P)
        #         elif len(aspect_length) == 4:
        #             pred_aspect_length4.append(aspect_P)
        #         elif len(aspect_length) >= 5:
        #             pred_aspect_length5.append(aspect_P)
        #
        #     gold_aspect_num_length1, pred_aspect_num_length1, correct_aspect_num_length1 = self.num_4_eval(
        #         gold_aspect_length1, pred_aspect_length1, gold_aspect_num_length1, pred_aspect_num_length1, correct_aspect_num_length1)
        #     gold_aspect_num_length2, pred_aspect_num_length2, correct_aspect_num_length2 = self.num_4_eval(
        #         gold_aspect_length2, pred_aspect_length2, gold_aspect_num_length2, pred_aspect_num_length2, correct_aspect_num_length2)
        #     gold_aspect_num_length3, pred_aspect_num_length3, correct_aspect_num_length3 = self.num_4_eval(
        #         gold_aspect_length3, pred_aspect_length3, gold_aspect_num_length3, pred_aspect_num_length3, correct_aspect_num_length3)
        #     gold_aspect_num_length4, pred_aspect_num_length4, correct_aspect_num_length4 = self.num_4_eval(
        #         gold_aspect_length4, pred_aspect_length4, gold_aspect_num_length4, pred_aspect_num_length4, correct_aspect_num_length4)
        #     gold_aspect_num_length5, pred_aspect_num_length5, correct_aspect_num_length5 = self.num_4_eval(
        #         gold_aspect_length5, pred_aspect_length5, gold_aspect_num_length5, pred_aspect_num_length5, correct_aspect_num_length5)
        #     assert gold_aspect_num_length1+gold_aspect_num_length2+gold_aspect_num_length3+gold_aspect_num_length4+gold_aspect_num_length5 == gold_aspect_num
        #
        #     for opinion_G in gold_opinion:
        #         opinion_length = opinion_G.split(' ')
        #         if len(opinion_length) == 1:
        #             gold_opinion_length1.append(opinion_G)
        #         elif len(opinion_length) == 2:
        #             gold_opinion_length2.append(opinion_G)
        #         elif len(opinion_length) >= 3:
        #             gold_opinion_length3.append(opinion_G)
        #         elif len(opinion_length) == 4:
        #             gold_opinion_length4.append(opinion_G)
        #         elif len(opinion_length) >= 5:
        #             gold_opinion_length5.append(opinion_G)
        #     for opinion_P in pred_opinion:
        #         opinion_length = opinion_P.split(' ')
        #         if len(opinion_length) == 1:
        #             pred_opinion_length1.append(opinion_P)
        #         elif len(opinion_length) == 2:
        #             pred_opinion_length2.append(opinion_P)
        #         elif len(opinion_length) >= 3:
        #             pred_opinion_length3.append(opinion_P)
        #         elif len(opinion_length) == 4:
        #             pred_opinion_length4.append(opinion_P)
        #         elif len(opinion_length) >= 5:
        #             pred_opinion_length5.append(opinion_P)
        #
        #     gold_opinion_num_length1, pred_opinion_num_length1, correct_opinion_num_length1 = self.num_4_eval(
        #         gold_opinion_length1, pred_opinion_length1, gold_opinion_num_length1, pred_opinion_num_length1,
        #         correct_opinion_num_length1)
        #     gold_opinion_num_length2, pred_opinion_num_length2, correct_opinion_num_length2 = self.num_4_eval(
        #         gold_opinion_length2, pred_opinion_length2, gold_opinion_num_length2, pred_opinion_num_length2,
        #         correct_opinion_num_length2)
        #     gold_opinion_num_length3, pred_opinion_num_length3, correct_opinion_num_length3 = self.num_4_eval(
        #         gold_opinion_length3, pred_opinion_length3, gold_opinion_num_length3, pred_opinion_num_length3,
        #         correct_opinion_num_length3)
        #     gold_opinion_num_length4, pred_opinion_num_length4, correct_opinion_num_length4 = self.num_4_eval(
        #         gold_opinion_length4, pred_opinion_length4, gold_opinion_num_length4, pred_opinion_num_length4,
        #         correct_opinion_num_length4)
        #     gold_opinion_num_length5, pred_opinion_num_length5, correct_opinion_num_length5 = self.num_4_eval(
        #         gold_opinion_length5, pred_opinion_length5, gold_opinion_num_length5, pred_opinion_num_length5,
        #         correct_opinion_num_length5)
        #     assert gold_opinion_num_length1+gold_opinion_num_length2+ gold_opinion_num_length3+gold_opinion_num_length4+gold_opinion_num_length5 == gold_opinion_num
        #
        # if self.args.output_path:
        #     F = open(self.args.dataset + 'triples.json', 'w', encoding='utf-8')
        #     json.dump(result, F, ensure_ascii=False, indent=4)
        #     F.close()
        #
        #     F1 = open(self.args.dataset + 'aspect.json', 'w', encoding='utf-8')
        #     json.dump(aspect_text, F1, ensure_ascii=False, indent=4)
        #     F1.close()
        #
        #     F2 = open(self.args.dataset + 'opinion.json', 'w', encoding='utf-8')
        #     json.dump(opinion_text, F2, ensure_ascii=False, indent=4)
        #     F2.close()

        # aspect_result_length1 = self.P_R_F1(gold_aspect_num_length1, pred_aspect_num_length1, correct_aspect_num_length1)
        # aspect_result_length2 = self.P_R_F1(gold_aspect_num_length2, pred_aspect_num_length2,
        #                                     correct_aspect_num_length2)
        # aspect_result_length3 = self.P_R_F1(gold_aspect_num_length3, pred_aspect_num_length3,
        #                                     correct_aspect_num_length3)
        # aspect_result_length4 = self.P_R_F1(gold_aspect_num_length4, pred_aspect_num_length4,
        #                                     correct_aspect_num_length4)
        # aspect_result_length5 = self.P_R_F1(gold_aspect_num_length5, pred_aspect_num_length5,
        #                                     correct_aspect_num_length5)
        #
        # opinion_result_length1 = self.P_R_F1(gold_opinion_num_length1, pred_opinion_num_length1, correct_opinion_num_length1)
        # opinion_result_length2 = self.P_R_F1(gold_opinion_num_length2, pred_opinion_num_length2, correct_opinion_num_length2)
        # opinion_result_length3 = self.P_R_F1(gold_opinion_num_length3, pred_opinion_num_length3, correct_opinion_num_length3)
        # opinion_result_length4 = self.P_R_F1(gold_opinion_num_length4, pred_opinion_num_length4, correct_opinion_num_length4)
        # opinion_result_length5 = self.P_R_F1(gold_opinion_num_length5, pred_opinion_num_length5, correct_opinion_num_length5)
        #
        #
        #
        # print(gold_opinion_num_length1, pred_opinion_num_length1, correct_opinion_num_length1)
        # print(gold_opinion_num_length2, pred_opinion_num_length2, correct_opinion_num_length2)
        # print(gold_opinion_num_length3, pred_opinion_num_length3, correct_opinion_num_length3)
        #
        # print('one token opinion precision:', opinion_result_length1[0], "one token opinion recall: ", opinion_result_length1[1], "one token opinion f1: ",
        #       opinion_result_length1[2])
        # print('two token opinion precision:', opinion_result_length2[0], "two token opinion recall: ", opinion_result_length2[1], "two token opinion f1: ",
        #       opinion_result_length2[2])
        # print('three token opinion precision:', opinion_result_length3[0], "three token opinion recall: ", opinion_result_length3[1], "three token opinion f1: ",
        #       opinion_result_length3[2])
        # print('4 token opinion precision:', opinion_result_length4[0], "4 token opinion recall: ", opinion_result_length4[1], "4 token opinion f1: ",
        #       opinion_result_length4[2])
        # print('5 token opinion precision:', opinion_result_length5[0], "5 token opinion recall: ",
        #       opinion_result_length5[1], "5 token opinion f1: ",
        #       opinion_result_length5[2])


        aspect_result = self.P_R_F1(gold_aspect_num, pred_aspect_num, correct_aspect_num)
        opinion_result = self.P_R_F1(gold_opinion_num, pred_opinion_num, correct_opinion_num)
        apce_result = self.P_R_F1(gold_apce_num, pred_apce_num, correct_apce_num)
        pair_result = self.P_R_F1(gold_pairs_num, pred_pairs_num, correct_pairs_num)
        triplet_result = self.P_R_F1(gold_num, pred_num, correct_num)
        return aspect_result, opinion_result, apce_result, pair_result, triplet_result

    def find_token(self, bert_tokens, span):
        bert_tokens_4_span = bert_tokens[span[1]:span[2]+1]
        sub = ''
        for i, tokens in enumerate(bert_tokens_4_span):
            if i == 0:
                sub = tokens
            # elif '-' in tokens:
            #     sub = sub + tokens.lstrip("##")
            # elif "'" in tokens:
            #     sub = sub + tokens.lstrip("##")
            elif '##' in tokens:
                sub = sub + tokens.lstrip("##")
            else:
                sub = sub +" "+ tokens
        return sub

    def gold_token(self, tokens):
        sub = ''
        for i, token in enumerate(tokens):
            if i == 0:
                sub = token
            elif '##' in token:
                sub = sub + token.lstrip("##")
            else:
                sub = sub +" "+ token
        return sub

    def find_aspect_sentiment(self, sentence_index, bert_spans, span, aspect_sentiment, aspect_sentiment_logit):
        for bert_span_index, bert_span in enumerate(bert_spans):
            if span[1] == bert_span[0] and span[2] == bert_span[1]:
                sentiment_index = aspect_sentiment[sentence_index][bert_span_index]
                sentiment = id2sentiment[aspect_sentiment[sentence_index][bert_span_index]]
                sentiment_logit = aspect_sentiment_logit[sentence_index][bert_span_index][sentiment_index]
        return sentiment, sentiment_logit

    def find_opinion_sentiment(self, sentence_index, opinion_index, bert_spans, span, opinion_sentiment,
                               opinion_sentiment_logit):
        for bert_span_index, bert_span in enumerate(bert_spans):
            if span[1] == bert_span[0] and span[2] == bert_span[1]:
                sentiment_index = opinion_sentiment[sentence_index][opinion_index][bert_span_index]
                sentiment = id2sentiment[opinion_sentiment[sentence_index][opinion_index][bert_span_index]]
                sentiment_logit = opinion_sentiment_logit[sentence_index][opinion_index][bert_span_index][sentiment_index]
        return sentiment, sentiment_logit

    # 使用原始数据的代码
    def find_gold_triples(self, sentence_index, bert_spans, bert_tokens):
        triples_list,pair_list = [],[]
        aspect_list,opinion_list,apce_list = [],[],[]
        triples = self.gold_instances[sentence_index]['triples']
        for keys in triples:
            aspect, opinion = keys.split('|')
            aspect_tokens = []
            for aspect_token in aspect.split( ):
                token = self.tokenizer.tokenize(aspect_token)
                aspect_tokens += token
            new_aspect = self.gold_token(aspect_tokens)

            opinion_tokens = []
            for opinion_token in opinion.split( ):
                token = self.tokenizer.tokenize(opinion_token)
                opinion_tokens += token
            new_opinion = self.gold_token(opinion_tokens)

            sentiment = triples[keys][2]

            triples_list.append((new_aspect, new_opinion, sentiment.lower()))

            aspect_list.append((new_aspect))
            opinion_list.append((new_opinion))

            apce_list.append((new_aspect, sentiment))
            pair_list.append((new_aspect, new_opinion))
        return aspect_list, opinion_list, apce_list, pair_list, triples_list

    '''编码之后再解码的代码'''
    # def find_gold_triples(self, sentence_index, bert_spans, bert_tokens):
    #     triples_list = []
    #     aspect_list = []
    #     gold_aspect_span = self.gold_aspect[sentence_index]
    #     for j, gold_aspect in enumerate(gold_aspect_span):
    #         if gold_aspect[2]-gold_aspect[1]+1 > self.args.max_span_length:
    #             continue
    #         aspect = self.find_token(bert_tokens, gold_aspect)
    #         aspect_sentiment = self.find_aspect_sentiment(sentence_index, bert_spans, gold_aspect, self.gold_aspect_sentiment)
    #         aspect_list.append((aspect, aspect_sentiment))
    #         opinion_list = []
    #         for opinion_index in list(np.where(np.array(self.gold_opinion[sentence_index][j]) != 0)[0]):
    #             opinion_list.append(opinion_index)
    #         opinion_spans = [bert_spans[opinion_index] for opinion_index in opinion_list]
    #         for opinion_span in opinion_spans:
    #             opinion_span = (opinion_span[2], opinion_span[0], opinion_span[1])
    #             opinion = self.find_token(bert_tokens, opinion_span)
    #             opinion_sentiment = self.find_opinion_sentiment(sentence_index, j, bert_spans, opinion_span, self.gold_opinion)
    #             assert  aspect_sentiment == opinion_sentiment
    #             triples_list.append((aspect, opinion, aspect_sentiment))
    #     return triples_list,aspect_list

    def find_pred_triples(self, sentence_index, bert_spans, bert_tokens):
        triples_list, pair_list = [], []
        aspect_list, pred_opinion_list, apce_list = [], [], []
        pred_aspect_span = self.pred_aspect[sentence_index]
        # 去除重复的aspect
        new_aspect_span = []
        for i, pred_aspect in enumerate(pred_aspect_span):
            if len(new_aspect_span) == 0:
                new_aspect_span.append(pred_aspect)
            else:
                if pred_aspect[1] == new_aspect_span[-1][1]:
                    new_aspect_span[-1] = pred_aspect
                else:
                    new_aspect_span.append(pred_aspect)
        for j, pred_aspect in enumerate(new_aspect_span):
            aspect = self.find_token(bert_tokens, pred_aspect)
            aspect_sentiment, aspect_sentiment_logit = self.find_aspect_sentiment(sentence_index, bert_spans, pred_aspect,
                                                          self.pred_aspect_sentiment, self.pred_aspect_sentiment_logit)
            aspect_list.append((aspect))
            apce_list.append((aspect, aspect_sentiment))
            opinion_list = []
            for opinion_index in list(np.where(np.array(self.pred_opinion[sentence_index][j]) != 0)[0]):
                opinion_list.append(opinion_index)
            opinion_spans = []
            for opinion_index in opinion_list:
                if opinion_index < len(bert_spans):
                    opinion_spans.append(bert_spans[opinion_index])
                else: continue
            new_opinion_spans = []
            for i, pred_opinion in enumerate(opinion_spans):
                if len(new_opinion_spans) == 0:
                    new_opinion_spans.append(pred_opinion)
                else:
                    if pred_opinion[1] == new_opinion_spans[-1][1]:
                        new_opinion_spans[-1] = pred_opinion
                    else:
                        new_opinion_spans.append(pred_opinion)
            for opinion_span in new_opinion_spans:
                opinion_span = (opinion_span[2], opinion_span[0], opinion_span[1])
                opinion = self.find_token(bert_tokens, opinion_span)
                opinion_sentiment, opinion_sentiment_logit = self.find_opinion_sentiment(sentence_index, j, bert_spans, opinion_span,
                                                                self.pred_opinion, self.pred_opinion_sentiment_logit)
                if opinion_sentiment_logit > aspect_sentiment_logit:
                    sentiment = opinion_sentiment
                else:
                    sentiment = aspect_sentiment

                pred_opinion_list.append((opinion))
                triples_list.append((aspect, opinion, sentiment))
                # triples_list.append((aspect, opinion, aspect_sentiment))
                # triples_list.append((aspect, opinion, opinion_sentiment))
                pair_list.append((aspect, opinion))
        return  aspect_list, pred_opinion_list, apce_list, pair_list, triples_list



if __name__ == '__main__':
    test1 = ('boot time', 'fast', 'pos')
    test = ('boot time', 'boot')
    test2 = ('Boot time', 'fast', 'pos')
    set1  = set(test1) & set(test2)
    print(set(test))