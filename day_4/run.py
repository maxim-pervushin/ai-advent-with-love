
import asyncio

from dotenv import load_dotenv
from providers.config import PROVIDER_CONFIGS, get_provider_config
from providers.factory import ProviderFactory

PROMPT_FAST = """Представь, что отвечаешь на викторине с таймером на 3 секунды. Напиши единственный вариант ответа без раздумий. Не используй слова «возможно», «вероятно», «зависит»."""

PROMPT_STEP_BY_STEP = "Решай задачу по-шагам"

PROMPT_ROLES = """Ты — Координатор Команды Экспертов. У тебя есть 4 эксперта:
1. АНАЛИТИК: анализирует факты, данные и логику. Всегда ищет противоречия.
2. КРИТИК: проверяет идеи на слабости, ошибки и риски. Никогда не соглашается сразу.
3. ГЕНЕРАТОР: предлагает креативные решения и идеи без ограничений.
4. СИНТЕЗИР: объединяет мнения в финальное решение, обосновывая выбор.

Процесс на ВСЕ задачи:
1. АНАЛИТИК разбирает запрос за 3 шага и дает факты.
2. ГЕНЕРАТОР предлагает 3+ варианта решений.
3. КРИТИК оценивает каждый вариант (плюсы/минусы).
4. СИНТЕЗИР формирует итог с обоснованием.
Отвечай ОТ ИМЕНИ каждого эксперта отдельно, четко разделяя. Финал — только от СИНТЕЗИРа."""

async def main(system_prompts: list[str | None], prompts: list[str]):
    providers = ("YandexCloud",)
    # providers = ("Mistral","YandexCloud",)
    for system_prompt in system_prompts:
        for prompt in prompts:
            for provider_name in providers:
                model = PROVIDER_CONFIGS[provider_name]["default_model"]
                provider = ProviderFactory.create_provider(provider_name)
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                print(f"System: {"None" if system_prompt is None else system_prompt[:25]}...")
                print(f"User: {prompt[:50]}...")
                response = await provider.call_api(messages=messages, model=model)
                print(f"AI: {response}")
                print("-" * 50)

if __name__ == "__main__":
    system_prompts = [
        PROMPT_FAST,
        PROMPT_STEP_BY_STEP,
        PROMPT_ROLES,
    ]

    prompts = [
        # "2 + 2 * 2",
        # "Какая дата будет через 20 дней, если сегодня - 15 января?",
        # "Сколько месяцев в году имеют 28 дней?",
        # "С какой скоростью должна двигаться собака (в возможных для неё пределах), чтобы не слышать звона сковородки, привязанной к ее хвосту?",
        # "Есть две бутыли. Первая – на 5 литров, вторая – на 3. Наберите в одну из бутылей ровно четыре литра. Запас воды не ограничен.",
        # "12+6÷2×3−4×(5−2)",
        "Три друга — Антон, Борис и Виктор — работают программистом, дизайнером и менеджером. Антон не менеджер. Борис не программист. Кто дизайнер?",
    ]
    
    asyncio.run(main(system_prompts, prompts))