module abs_diff_i53248_o26624(a,b,r);
input [26623:0] a,b;
output [26623:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
