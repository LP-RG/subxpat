module bin_squared_i16_o18 (a, b, r);
input [7:0] a, b;
output [17:0] r;


assign r = (a - b) * (a - b);

endmodule 
 
