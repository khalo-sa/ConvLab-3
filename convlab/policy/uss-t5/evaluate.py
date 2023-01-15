import os
from argparse import ArgumentParser
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from sklearn import metrics
from tqdm import tqdm
from transformers import T5ForConditionalGeneration, T5Tokenizer


def arg_parser():
    parser = ArgumentParser()
    parser.add_argument("--model", type=str, default="",
                        help="model name")
    parser.add_argument("--data", type=str)

    return parser.parse_args()


def bi_f1(x):
    if x in ['1', '2']:
        return 0
    elif x in ['3', '4', '5']:
        return 1
    else:
        return 0


def main():
    args = arg_parser()
    model_checkpoint = args.model
    tokenizer = T5Tokenizer.from_pretrained(model_checkpoint)
    model = T5ForConditionalGeneration.from_pretrained(model_checkpoint)
    data = pd.read_csv(args.data, index_col=False).astype(str)

    preds = {'bi': [], "five": []}
    label = {'bi': [], "five": []}

    for input_text, target_text in tqdm(zip(data["input_text"], data["target_text"]), ascii=True):
        if "satisfaction score" in input_text:
            inputs = tokenizer([input_text], return_tensors="pt", padding=True)
            output = model.generate(input_ids=inputs["input_ids"],
                                    attention_mask=inputs["attention_mask"],
                                    do_sample=False)
            output = tokenizer.batch_decode(output, skip_special_tokens=True)[0]
            if len(output) > 1:
                print(output)
                output = "illegal"
            label["five"].append(target_text)
            preds["five"].append(output)
            label["bi"].append(bi_f1(target_text))
            preds["bi"].append(bi_f1(output))

    macro_f1 = metrics.f1_score(label["five"], preds["five"], average="macro")
    f1 = metrics.f1_score(label["bi"], preds["bi"])
    sep_f1 = metrics.f1_score(
        label["five"], preds["five"], average=None,
        labels=['1', '2', '3', '4', '5'])
    cm = metrics.confusion_matrix(
        label["five"], preds["five"], normalize="true",
        labels=['1', '2', '3', '4', '5'])
    disp = metrics.ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=['1', '2', '3', '4', '5'])
    disp.plot()
    dirname = "convlab/policy/uss-t5/"
    time = f"{datetime.now().strftime('%y-%m-%d-%H-%M')}"
    plt.savefig(os.path.join(dirname, model_checkpoint, f"{time}-emotion.png"))
    r = {"macro_f1": float(macro_f1),
         "bi_f1": float(f1),
         "sep_f1": list(sep_f1),
         "cm": [list(c) for c in list(cm)]}
    print(r)


if __name__ == "__main__":
    main()
