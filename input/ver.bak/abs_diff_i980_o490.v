module abs_diff_i980_o490(a,b,r);
input [489:0] a,b;
output [489:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
