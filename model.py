import torch
from transformers import BertForQuestionAnswering, BertTokenizer, pipeline
import textwrap



def answer_question(question, answer_text):
    print('\n###### ANSWER QUESTION ######')
    input_ids = tokenizer.encode(question, answer_text)
    sep_index = input_ids.index(tokenizer.sep_token_id)
    num_seg_a = sep_index + 1
    num_seg_b = len(input_ids) - num_seg_a
    segment_ids = [0]*num_seg_a + [1]*num_seg_b
    assert len(segment_ids) == len(input_ids)
    start_scores, end_scores = model(torch.tensor([input_ids]), token_type_ids=torch.tensor([segment_ids]))
    answer_start = torch.argmax(start_scores)
    answer_end = torch.argmax(end_scores)
    tokens = tokenizer.convert_ids_to_tokens(input_ids)
    answer = tokens[answer_start]
    for i in range(answer_start + 1, answer_end + 1):
        if tokens[i][0:2] == '##':
            answer += tokens[i][2:]
        else:
            answer += ' ' + tokens[i]
    print('\tQuery has {:,} tokens.'.format(len(input_ids)))
    print('\tSoru: "' + question + '"')
    print('\tCevap: "' + answer + '"')

if __name__ == '__main__':
    output_dir = 'model'
    model = BertForQuestionAnswering.from_pretrained(output_dir)
    tokenizer = BertTokenizer.from_pretrained(output_dir)


    text='''Sanat tarihçileri için devasa bir konu olan Leonardo da Vinci’nin tablosu Mona Lisa, medeniyetinin sahip olduğu en özel parçalardan biri.
Mona Lisa tablosunda resmedilmiş kişinin gerçek ismi Lisa Gherardini. Mona Lisa, “benim kadınım Lisa” anlamına geliyor.
Orijinal tablonun boyutları 77×53 cm.
Mona Lisa tablosunun başka bir adı daha var: La Gioconda. Bu isim ise Mona Lisa’nın “Wife of Francesco del Giocondo” yani Frances del Giocondo’nun Karısı unvanına sahip olması nedeniyle verilmiş. Kesin olmamakla birlikte Mona Lisa’nın gerçekte Lisa del Giocondo olduğu düşünülüyor.
Mona Lisa tablosunun herhangi bir sigortası yok. Bunun nedeni de sigortalanamayacak kadar değerli görülmesi. Hiçbir sigorta şirketi bu riske girmek istemiyor yani.
Yüz tanımada kullanılan sisteme göre Mona Lisa’nın yüzü %83 mutlu, %9 bıkkın, %6 korkmuş ve %2 sinirli mimiklere sahip.
Mosa Lisa tablosu, ilk önce Fransa kralı I. Francis’e (I. François) satılmış. Leonardo’nun başyapıtı, kralın isteği üzerine Fontainebleau Sarayı’nda sergilenmiş.
Mona Lisa tablosu, sanat tarihçileri tarafından her zaman ön planda tutulsa da küresel ününü 1911 yılında onu çalan hırsıza borçlu.
Mona Lisa, Fransa’nın en ünlü müzesi olan Louvre’da, tabloya özel tasarlanmış bir odada sergileniyor.'''

    answer_question("Tablonun boyutları nedir?", text)

    answer_question("Mona lisa tablosu nerededir?", text)
