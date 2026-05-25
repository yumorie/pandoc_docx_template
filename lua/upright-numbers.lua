function Math(el)
    local text = el.text

    io.stderr:write("[upright-numbers] before: " .. text .. "\n")
  
    text = text:gsub("(%d+%.?%d*)", "\\mathrm{%1}")

    io.stderr:write("[upright-numbers] after: " .. text .. "\n")
  
    return pandoc.Math(el.mathtype, text)
  end

  return { Math = Math }