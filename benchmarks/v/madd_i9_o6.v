module madd_i9_o6 (a, b, c, r);
input [2:0] a, b, c;
output [5:0] r;


assign r = (a * b) + c;

endmodule  
