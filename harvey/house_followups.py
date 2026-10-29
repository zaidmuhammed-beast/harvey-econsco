"""Fixed follow-up emails (steps 2 and 3), used instead of model-written ones.

The model kept drifting in follow-ups: switching from "freelance WordPress
developer" to "our agency team", and inventing client stories. These are
plain, honest, website-only follow-ups. Merge variables are filled per
prospect by the sender ({{first_name}} becomes "there" for general inboxes).
"""

from harvey.models.campaign import EmailStep

FOLLOWUP_2_SUBJECT = "{{company}}'s website"
FOLLOWUP_2_BODY = """Hi {{first_name}},

Following up with something concrete. For a business like {{company}}, the three changes that usually make the biggest difference are a faster mobile site, a clear "book / get a quote" button on every page, and Google showing your hours and reviews properly.

Happy to check which of these apply to your site and send a short note. Just reply "yes".

Arslan"""
FOLLOWUP_2_DELAY_DAYS = 3

FOLLOWUP_3_SUBJECT = "closing the loop"
FOLLOWUP_3_BODY = """Hi {{first_name}},

I won't keep emailing. If improving the website becomes a priority later, just reply here and I'll send over a few ideas.

All the best,
Arslan"""
FOLLOWUP_3_DELAY_DAYS = 4


def house_followup_steps() -> list[EmailStep]:
    return [
        EmailStep(step=2, subject=FOLLOWUP_2_SUBJECT, body=FOLLOWUP_2_BODY,
                  delay_days=FOLLOWUP_2_DELAY_DAYS),
        EmailStep(step=3, subject=FOLLOWUP_3_SUBJECT, body=FOLLOWUP_3_BODY,
                  delay_days=FOLLOWUP_3_DELAY_DAYS),
    ]


def with_house_followups(sequence: list[EmailStep]) -> list[EmailStep]:
    """Keep the model's step 1 (if any); replace everything after it."""
    first = [s for s in sequence if s.step == 1][:1]
    return first + house_followup_steps()
