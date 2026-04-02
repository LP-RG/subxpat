module madd_i21_o14 (a, b, c, r);
input [6:0] a, b, c;
output [13:0] r;


assign r = (a * b) + c;

endmodule  
