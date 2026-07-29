<?xml version="1.0" ?>
<qgis version="3.34" styleCategories="AllStyleCategories">
  <pipe>
    <rasterrenderer type="singlebandpseudocolor" band="1" opacity="1" alphaBand="-1" classificationMin="0" classificationMax="50" nodataColor="#ffffff">
      <rastershader>
        <colorrampshader colorRampType="DISCRETE" classificationMode="1" clip="0" labelPrecision="2" minimumValue="0" maximumValue="50">
          <item value="1" label="&lt;   1 year" color="#a80000" alpha="255"/>
          <item value="2" label="&lt;   2 years" color="#ff0000" alpha="255"/>
          <item value="5" label="&lt;   5 years" color="#fc8b00" alpha="255"/>
          <item value="10" label="&lt; 10 years" color="#fcc200" alpha="255"/>
          <item value="15" label="&lt; 15 years" color="#f5f500" alpha="255"/>
          <item value="20" label="&lt; 20 years" color="#c6f700" alpha="255"/>
          <item value="30" label="&lt; 30 years" color="#94f700" alpha="255"/>
          <item value="40" label="&lt; 40 years" color="#4ce600" alpha="255"/>
          <item value="50" label="&lt; 50 years" color="#38a800" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <nodata/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
