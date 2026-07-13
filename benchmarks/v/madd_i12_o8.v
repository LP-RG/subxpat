module madd_i12_o8 (a, b, c, r);
input [3:0] a, b, c;
output [7:0] r;


assign r = (a * b) + c;

endmodule  
