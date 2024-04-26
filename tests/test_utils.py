from pathlib import Path

from audio_para_texto.utils import transcribe_audio


def test_transcribe_audio():
    result = transcribe_audio(str(Path('tests') / 'audio.mp3'))
    expected = 'Eu coloquei um ssd no play 4 pro e você não vai acreditar como melhorou. Olá pessoal sou gabriel de pinho e depois de colocar ssd em um play 4 pet em um play 3 slim e em até o playstation 2. Se você não viu dá uma olhada na descrição. Tá na hora de testar. Esse pequeno. Ssd né faz diferença em um playstation 4 pro. Videogame que tem um hacker mais forte. E dizem conseguir extrair.'
    assert result == expected
