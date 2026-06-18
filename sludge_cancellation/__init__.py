from otree.api import *
import itertools
import random

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
    # Флаг отмены подписки в текущем раунде
    cancelled_this_round = models.BooleanField(initial=False)


    # PAGES
class Task(Page):
    form_model = 'player'
    form_fields = [
        'player_answer', 
        'round_time_penalty', 
        'cabinet_time_round', 
        'clicks_count', 
        'validation_errors', 
        'cabinet_opened',
        'cancelled_this_round' # Добавили новое поле
    ]

    @staticmethod
    def vars_for_template(player: Player):
        # Генерируем уникальную матрицу 10х10
        matrix = []
        zeros_count = 0
        for _ in range(10):
            row = []
            for _ in range(10):
                val = random.choice([0, 1])
                if val == 0:
                    zeros_count += 1
                row.append(val)
            matrix.append(row)
        
        # Сохраняем правильный ответ в базу
        player.matrix_correct_answer = zeros_count
        
        # Уведомление показывается только перед 3-м раундом
        show_warning = (player.round_number == 3)
        
        return {
            'matrix': matrix,
            'show_warning': show_warning,
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # 1. Обновляем глобальный статус подписки, если участник её отменил
        if player.cancelled_this_round:
            player.participant.subscription_active = False
            
        # Фиксируем статус подписки для логов этого раунда
        player.subscription_active = player.participant.subscription_active

        # 2. Проверка правильности подсчета нулей
        player.is_correct = (player.player_answer == player.matrix_correct_answer)
        base_reward = Constants.base_matrix_reward if player.is_correct else cu(0)
        
        # 3. Списание за подписку (начиная с 3 раунда, если активна)
        sub_cost = cu(0)
        if player.round_number >= 3 and player.subscription_active:
            sub_cost = Constants.subscription_cost
        
        # 4. Расчет итогового заработка
        final_payoff = base_reward - cu(player.round_time_penalty) - sub_cost
        
        player.round_payoff_eve = int(final_payoff)
        player.payoff = final_payoff

page_sequence = [Task]