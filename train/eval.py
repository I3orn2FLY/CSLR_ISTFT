import torch
from train.train_end2end import get_end2end_model
from config import *
from utils import Vocab


# TODO fix eval

def decode_prediction(pred, vocab):
    pred = pred.permute(1, 0, 2).squeeze(0).argmax(dim=1).cpu().numpy()

    out_sentence = []
    start_times = []
    durations = []

    duration = 1
    step = 4
    for i in range(len(pred)):
        if pred[i] == 0 or (i > 0 and pred[i] == pred[i - 1]):
            duration += step
            continue

        durations.append(duration / 25)
        duration = step
        start_times.append(i * step / 25)
        out_sentence.append(vocab.idx2gloss[pred[i]])

    durations.append(duration / 25)
    durations = durations[1:]
    return out_sentence, start_times, durations


def create_ctm_file_split(model, vocab, split):
    gt_ctm_val_file = os.sep.join([PH_EVA_DIR, "phoenix2014-groundtruth-" + split + ".stm"])

    with open(gt_ctm_val_file, 'r') as f:
        lines = f.readlines()

    dirs = []
    for line in lines:
        dirs.append(line.split(" ")[0])

    out_ctm_path = STF_MODEL + "_" + split + ".ctm"
    with open(os.sep.join([PH_EVA_DIR, out_ctm_path]), 'w') as f:

        with torch.no_grad():
            for idx, dir in enumerate(dirs):
                feat_path = os.sep.join([STF_FEAT_DIR, split, dir + ".pt"])
                inp = torch.load(feat_path).to(DEVICE).unsqueeze(0)

                pred = model(inp).log_softmax(dim=2)

                out_sentence, start_times, durations = decode_prediction(pred, vocab)
                for gloss, start_time, duration in zip(out_sentence, start_times, durations):
                    f.write(" ".join([dir, "1", "%.3f" % start_time, "%.3f" % duration, gloss]) + os.linesep)


if __name__ == "__main__":
    vocab = Vocab()
    model, loaded = get_end2end_model(vocab, load=True, stf_type=1)
    if not loaded:
        print("STF or SEQ2SEQ model doesn't exist")
        exit(0)
    model.eval()
    with torch.no_grad():
        create_ctm_file_split(model, vocab, "test")
        create_ctm_file_split(model, vocab, "dev")
