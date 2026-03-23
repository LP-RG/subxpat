module madd_i6_o4 (a, b, c, r);
input [1:0] a, b, c;
output [3:0] r;


assign r = (a * b) + c;

endmodule  
