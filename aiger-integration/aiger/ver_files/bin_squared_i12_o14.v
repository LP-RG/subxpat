module bin_squared_i12_o14 (a, b, r);
input [5:0] a, b;
output [13:0] r;


assign r = (a - b) * (a - b);

endmodule 
 
