import model
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("command", nargs="?", default="all")
parser.add_argument("text", nargs="*")

args = parser.parse_args()

if args.command == "predict":
    text = " ".join(args.text)
    score = model.predict(text)
    desc = "positive" if score > 0.5 else "negative"
    print(f"score is: {score:0.2f} ({desc} sentiment)")


elif args.command == "train":
    model.train()

elif args.command == "upload":
    model.upload_tokenizer()
    model.upload_model()

elif args.command == "download":
    model.download_model()

elif args.command == "all":
    model.train()
    model.upload_tokenizer()
    model.upload_model()

else:
    raise ValueError(f"unknown command {args.command}")
