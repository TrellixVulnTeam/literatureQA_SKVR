import tokenization
import sys
import os
from multiprocessing import Pool
from nltk.tokenize import sent_tokenize
import math

vocab_file = "code/models/pretrain_base/vocab.txt"
do_lower_case = True
input_folder = "preprocess/corpus"

tokenizer = tokenization.FullTokenizer(
      vocab_file=vocab_file, do_lower_case=do_lower_case)

file_list = []
for path, _, filenames in os.walk(input_folder):
    for filename in filenames:
        file_list.append(os.path.join(path, filename))

part = int(math.ceil(len(file_list) / 20.))
file_list = [file_list[i:i+part] for i in range(0, len(file_list), part)]

sep_id = tokenizer.convert_tokens_to_ids(["sepsepsep"])[0]

# 00 Add
special_token = {"[unused1]", "[unused2]", "[unused3]", "[unused4]", "[unused5]"}
# End Add

# load entity dict
d_ent = {}
with open("preprocess/alias_entity.txt", "r") as fin:
    for line in fin:
        v = line.strip().split("\t")
        if len(v) != 2:
            continue
        d_ent[v[0]] = v[1]

def run_proc(idx, n, file_list):
    folder = "preprocess/raw"
    for i in range(len(file_list)):
        if i % n == idx:
            target = "{}/{}".format(folder, i)
            fout_text = open(target+"_token", "w")
            fout_ent = open(target+"_entity", "w")
            input_names = file_list[i]
            for input_name in input_names:
                print(input_name)
                fin = open(input_name, "r")

                for doc in fin:
                    doc = doc.strip()
                    segs = doc.split("[_end_]")
                    content = segs[0]
                    # 01 Change
                    # sentences = sent_tokenize(content)
                    sentences = sent_tokenize(content[: content.find("sepsepsep")])
                    sentences.append(content[content.find("sepsepsep"): ])
                    # End Change
                    map_segs = segs[1:]
                    maps = {}
                    # 02 Change
                    # for x in map_segs:
                    #     v = x.split("[_map_]")
                    #     if len(v) != 2:
                    #         continue
                    #     if v[1] in d_ent:
                    #         maps[v[0]] = d_ent[v[1]]
                    map_counter = 0
                    for x in map_segs:
                        v = x.split("[_map_]")
                        maps[map_counter] = d_ent[v[1]]
                        map_counter += 1
                    # End Change
                    text_out = [len(sentences)]
                    ent_out = [len(sentences)]

                    # 03 Change
                    # for sent in sentences:
                    map_counter2 = 0
                    for sent_idx, sent in enumerate(sentences):
                    # End Change
                        # 04 Change
                        # tokens = tokenizer.tokenize(sent)
                        if sent_idx == len(sentences) - 1:
                            tokens = [x for x in [x.strip() for x in sent.split("sepsepsep")] if x != ""]
                        else:
                            tokens = tokenizer.tokenize(sent)
                        # End Change
                        anchor_segs = [x.strip() for x in sent.split("sepsepsep")]
                        # 05 Add
                        if sent_idx == len(sentences) - 1:
                            anchor_segs = [x for x in anchor_segs if x != ""]
                        # End Add
                        result = []
                        for x in anchor_segs:
                            # 06 Change
                            # if x in maps:
                            #     result.append(maps[x])
                            if x in special_token:
                                result.append(maps[map_counter2])
                                map_counter2 += 1
                            # End Change
                            else:
                                result.append("#UNK#")
                        cur_seg = 0

                        new_text_out = []
                        new_ent_out = []

                        for token in tokenizer.convert_tokens_to_ids(tokens):
                            if token != sep_id:
                                new_text_out.append(token)
                                new_ent_out.append(result[cur_seg])
                            else:
                                cur_seg += 1
                        
                        if len(new_ent_out) != 0:
                            ent_out.append(len(new_ent_out))
                            ent_out.extend(new_ent_out)
                            text_out.append(len(new_text_out))
                            text_out.extend(new_text_out)
                        else:
                            text_out[0] -= 1
                            ent_out[0] -= 1
                    assert map_counter == map_counter2
                    fout_ent.write("\t".join([str(x) for x in ent_out])+"\n")
                    fout_text.write("\t".join([str(x) for x in text_out])+"\n")
                fin.close()
            fout_ent.close()
            fout_text.close()

folder = "preprocess/raw"
if not os.path.exists(folder):
    os.makedirs(folder)

n = int(sys.argv[1])
p = Pool(n)
for i in range(n):
    p.apply_async(run_proc, args=(i,n, file_list))
p.close()
p.join()