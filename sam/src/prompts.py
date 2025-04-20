
def get_navigation_prompt(target_organ):
    """
    Returns the LLM prompt as a multi-line string.
    This prompt guides the LLM to generate a step-by-step voice instruction transcript
    that helps astronauts transition the ultrasound probe from imaging the current area
    to imaging a desired organ in a microgravity environment.
    """
    prompt = (
        "You are an astronaut assistant providing real-time, voice-based instructions to non-expert astronauts "
        "in space who are operating the NASA Ultrasound-2 system. Your task is to guide them step-by-step on how to "
        "smoothly transition the ultrasound probe from imaging the current anatomical area to imaging a desired area. "
        "The astronauts work in a microgravity environment, so your instructions must address key challenges such as "
        "securing equipment and maintaining stability.\n\n"
        "Desired Organ: {target_organ}\n\n"
        "Your instructions should include the following details:\n\n"
        
        "1. Current Image Verification:\n"
        "   - Clearly instruct the user to confirm that the currently displayed image (the current imaging area) is stable "
        "   and properly defined.\n"
        "   - Provide a brief pause for the astronaut to verify and understand the current setup.\n\n"
        
        "2. Preparing for the Transition:\n"
        "   - Instruct how to maintain contact with the patient's skin and prepare to move the probe.\n"
        "   - Instruct how to position the patient and what direction to give to the patient.\n\n"
        
        "3. Probe Movement:\n"
        "   - Guide the astronaut to slowly and smoothly move the probe from its current position toward the new, desired area.\n"
        "   - Include clear directions about the movement path (for example, 'move upward' or 'shift laterally'), "
        "adapted to the specifics of the transition at hand.\n"
        "   - Mention the importance of deliberate, slow adjustments to avoid losing contact or disrupting the image.\n\n"
        
        "4. Acquiring the Desired Organ Image:\n"
        "   - Instruct on how to identify anatomical landmarks that indicate the probe has reached the desired imaging window.\n"
        "   - Specify adjustments such as angling the probe or making small rotations (clockwise or counterclockwise) as needed "
        "until the desired area's details are visible.\n"
        "   - Explain how to use key system settings like depth, gain, and frequency to optimize the image.\n\n"
        
        "5. Final Verification and Stabilization:\n"
        "   - Instruct the astronaut to confirm that the desired area is clearly visible and that key features are identifiable.\n"
        
        "The tone of the instructions should be calm, confident, and clear, using non-technical language whenever possible. "
        "The output must be a transcript that can be read aloud, with each step clearly separated. The transcript should "
        "include occasional reflective questions to confirm the astronaut's understanding.\n\n"
        
        "Now, generate the complete voice instruction transcript based on these guidelines."
    )
    return prompt.format(target_organ=target_organ)


def get_ultrasound_diagnostic_prompt(target_organ):
    """
    Returns the LLM prompt as a multi-line string.
    This prompt directs a voice agent to review an ultrasound image provided by an astronaut.
    The voice agent should evaluate image quality, comment on the viewable area, and offer an initial diagnostic assessment.
    """
    prompt = """
    You are an agent reviewing an ultrasound scan sent by an astronaut. Your task is to provide a clear and supportive written transcript focused on evaluating the organ shown in the image.

    The target organ appears to be {target_organ}.

    Your response should include the following sections:

    1. Observations of the Organ:

    Briefly describe the organ's overall appearance—shape, size, and texture.

    Note any visible features like vessels, ducts, chambers, or differences in echogenicity.

    Mention any landmarks that help confirm the organ's identity.

    2. Initial Diagnostic Impression:

    Comment on whether the organ appears normal or if there are signs of concern (e.g., irregular texture, unclear boundaries, fluid presence).

    Suggest if further imaging or clarification might be needed.

    3. Recommendations:

    Offer simple next steps, such as adjusting the probe, changing the angle, or capturing another view.

    Ask a quick follow-up question to confirm understanding or readiness to continue.

    Keep the response concise, medically appropriate, and easy for the astronaut to follow in a high-stress environment. Format the output in plain text.
    """
    return prompt.format(target_organ=target_organ)


