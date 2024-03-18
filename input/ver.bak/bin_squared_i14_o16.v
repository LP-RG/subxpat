module bin_squared_i14_o16 (a, b, r);
input [6:0] a, b;
output [15:0] r;


assign r = (a - b) * (a - b);

endmodule 
 
