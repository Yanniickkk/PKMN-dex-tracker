namespace LivingDex.Core.Reference;

/// <summary>
/// Where a piece of acquisition data came from. Every <see cref="AcquisitionMethod"/> carries
/// one, so a disputed encounter rate can be traced back without rerunning the pipeline.
/// </summary>
/// <param name="Source">Short name of the source, for example <c>bulbapedia</c> or <c>pokeapi</c>.</param>
/// <param name="Url">The exact page or endpoint, when there is one.</param>
/// <param name="RetrievedOn">The day the pipeline read it.</param>
public sealed record SourceCitation(string Source, Uri? Url, DateOnly RetrievedOn);
