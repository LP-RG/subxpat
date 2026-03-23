module madd_i15_o10 (a, b, c, r);
input [4:0] a, b, c;
output [9:0] r;


assign r = (a * b) + c;

endmodule  
