from otree.api import *
import itertools

doc = """
Влияние деструктивной архитектуры выбора (сладжа) на отмену цифровых подписок.
"""

class Constants(BaseConstants):
    name_in_url = 'sludge_cancellation'
    players_per_group = None
    num_rounds = 10 # 10 рабочих раундов
    base_matrix_reward = cu(100) # Базовое вознаграждение за правильную матрицу
    subscription_cost = cu(15) # Стоимость премиум-ассистента

class Subsession(BaseSubsession):
    pass

def creating_session(subsession: Subsession):
    if subsession.round_number == 1:
        # Создаем цикл для рандомизации 1:1 (True = сладж, False = контроль)
        treatments = itertools.cycle([True, False])
        for player in subsession.get_players():
            # Записываем группу в participant, чтобы она сохранялась между раундами
            player.participant.is_sludge = next(treatments)
            # глобальный статус подписки (по умолчанию активна)
            player.participant.subscription_active = True
            
    # значение из participant в player для экспорта данных логов
    for player in subsession.get_players():
        player.is_sludge = player.participant.is_sludge
        player.subscription_active = player.participant.subscription_active

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    # Идентификаторы группы и статусы 
    is_sludge = models.BooleanField()
    subscription_active = models.BooleanField()
    
    # Переменные основной задачи (матрицы)
    matrix_correct_answer = models.IntegerField()
    player_answer = models.IntegerField(blank=True, null=True)
    is_correct = models.BooleanField(initial=False)
    round_time_penalty = models.IntegerField(initial=0) # Штраф за время (1 ЭВЕ/сек)
    round_payoff_eve = models.IntegerField(initial=0) # Итоговый заработок за раунд в ЭВЕ
    
    # Метрики личного кабинета и сладжа
    cabinet_time_round = models.IntegerField(initial=0) # Совокупное время в кабинете (сек)
    clicks_count = models.IntegerField(initial=0) # Количество кликов мышью
    validation_errors = models.IntegerField(initial=0) # Ошибки ввода кодового слова
    cabinet_opened = models.BooleanField(initial=False) # Открывал ли кабинет в этом раунде
    
    # Финальная анкета
    gender = models.StringField(
        choices=[['Мужской', 'Мужской'], ['Женский', 'Женский']],
        label='Укажите ваш пол:',
        blank=True
    )
    admin_lit_1 = models.IntegerField(
        choices=[1, 2, 3, 4, 5], widget=widgets.RadioSelect, blank=True,
        label='1. Я обычно легко понимаю правила электронных подписок и контрактов.'
    )
    admin_lit_2 = models.IntegerField(
        choices=[1, 2, 3, 4, 5], widget=widgets.RadioSelect, blank=True,
        label='2. Я всегда внимательно читаю условия автоматического продления перед тем, как привязать банковскую карту.'
    )
    admin_lit_3 = models.IntegerField(
        choices=[1, 2, 3, 4, 5], widget=widgets.RadioSelect, blank=True,
        label='3. При необходимости я уверенно ориентируюсь в настройках цифровых сервисов, даже если они запутаны.'
    )
    purpose_guess = models.LongStringField(
        label='Как Вы думаете, что проверялось в ходе этого исследования?',
        blank=True
    )