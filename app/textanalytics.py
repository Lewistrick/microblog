from collections import Counter
from nltk import word_tokenize
from time import sleep

def word_counts(text):
	sleep(1)
	# words = word_tokenize(text)
	counts = Counter(text.lower())
	return \
		"<hr /><p>Meest voorkomende letters:</p>" + \
		"<br />".join(
			['<b>{}</b> komt <b>{}</b> keer voor'.format(elem, count)
			for elem, count in counts.most_common(10)
			if elem.isalpha()]
		)
