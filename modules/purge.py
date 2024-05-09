from telethon.tl.functions.channels import DeleteMessagesRequest, GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator

from ._config import OWNER_ID, bot
from ._handler import new_cmd


async def can_purge(chat, user):
    if user.id == OWNER_ID:
        return True

    try:
        participant = await bot(GetParticipantRequest(chat, user))
        if isinstance(participant.participant, ChannelParticipantCreator):
            return True
        elif isinstance(participant.participant, ChannelParticipantAdmin):
            if participant.participant.admin_rights is not None:
                return participant.participant.admin_rights.delete_messages
            return False
        return False
    except:
        return False


@new_cmd(pattern="purge$")
async def purge(event):
    if not event.is_group:
        return
    if not await can_purge(event.chat_id, event.sender_id):
        return
    till_id = 0
    if event.is_reply:
        till_id = event.reply_to_msg_id
    else:
        try:
            args = event.text.split(" ", 1)[1]
            till_id = int(args)
        except:
            pass

    if till_id == 0:
        await event.reply(
            "Please reply to a message or provide a message id to purge till."
        )

    try:
        req = DeleteMessagesRequest(event.chat_id, [i for i in range(till_id)])
        await bot(req)
    except Exception as e:
        await event.reply(f"Failed to purge messages: {e}")
