module madd_i18_o12 (a, b, c, r);
input [5:0] a, b, c;
output [11:0] r;


assign r = (a * b) + c;

endmodule  
