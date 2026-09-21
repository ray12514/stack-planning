# CSE software delivery: management talking points

**September 18, 2026**

**Position:** Continue CSE's existing user-space software delivery model with
Spack. Do not make its adoption the entry point for requiring all research
software to come through centrally vetted local repositories.

## CSE's operating model

1. **Spack improves an established method of delivering software.** CSE already
   obtains, builds, and maintains scientific packages in user space. The proposed
   use of Spack automates that work without adding administrative privileges.
   Assess changes in executable inputs and workflow against that existing model.

2. **CSE can control its build stages through its own group permissions.**
   Restricted working areas keep unfinished software separate from published
   releases. Recorded inputs, integrity checks, technical review, and testing
   support accountable delivery. These safeguards do not depend on prohibiting
   external sources. Group permissions govern access; code still runs with the
   builder account's permissions.

3. **Address specific Spack risks without making every source a central admission
   decision.** Recipes, dependencies, and bootstrap tools deserve scrutiny.
   The SOP draft supports review focused on relevant changes and findings, rather
   than manual examination of every recipe and dependency on every build.
   That provides a practical basis for improving CSE's current process.

## The case against an exclusive vetted-repository requirement

4. **Local storage does not establish that software is safe.** A controlled
   repository can enforce selection and integrity checks. Its benefit depends
   on those checks, continued maintenance, and protection against compromise.
   The case for excluding all other sources must establish added protection
   beyond the controls CSE can apply within its existing workflow.

5. **“Vetted” must identify what was examined and what the checks establish.**
   Reviewing a recipe does not validate all the code it downloads. A checksum
   confirms expected bytes; a known-vulnerability scan checks reported issues.
   Neither establishes the absence of malicious code or undiscovered flaws.
   An approval label cannot stand in for defined evidence.

6. **Approving a repository and approving each revision create different problems.**
   If approval covers future changes automatically, those changes have not
   necessarily received the original scrutiny. If every revision and dependency
   needs approval, ongoing research becomes dependent on an approval service.
   The proposal must explain which model it requires and how it supports iteration.

7. **Older or previously approved software still needs security maintenance.**
   Flaws can remain undiscovered until long after approval. Holding a fixed
   software set does not remove that exposure, and an approval queue can delay
   corrective updates. Assess the ability to identify and address affected
   software throughout its use, not only at initial acceptance.

8. **Limit exposure and prepare to contain incidents within the existing model.**
   Keep unnecessary credentials and write access out of builds; retain component
   and execution records; hold suspect candidates; withdraw affected releases;
   preserve evidence and support incident response. Quarantine must address the
   affected accounts and execution as needed, not just move a file. Evidence
   determines the containment scope.

9. **Research demand does not stop at a predefined software list.** A collaborator's
   new commit, a Python dependency, or a compiler-specific fix can change what a
   researcher needs to build. Requiring prior approval for each change adds a
   service dependency. Staffing, turnaround, dependencies, and urgent fixes must
   be addressed before claiming that access can be restricted without hindering work.

10. **Do not establish a general restriction through the CSE decision.** Applying
    a local-only requirement to unprivileged CSE builds could set a precedent for
    Python environments and other user builds. Retain current acquisition and
    installation practices while addressing demonstrated risks with specific
    controls. Broader restrictions require their own mission and security case.

**Basis:** Responds to the proposal as described by CSE; the ISSM white paper
has not been supplied. SOP safeguards above are documented or proposed, not
claims of verified deployment. This talking-points revision changes no SOP.

**Supporting references:**
[CSE SOP: access and state separation](cse_software_stack_sop_v1.md#4-storage-access-and-spack-runtime)
(sections 2, 4, 8, 12–13);
[NIST SSDF: component evaluation throughout the lifecycle, PW.4.4](https://csrc.nist.gov/pubs/sp/800/218/final);
[pip-audit: known-vulnerability checks do not establish absence of malicious packages](https://github.com/pypa/pip-audit#security-model);
[NIST incident-response guidance](https://csrc.nist.gov/pubs/sp/800/61/r3/final).
